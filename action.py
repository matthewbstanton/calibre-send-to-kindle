"""The Send to Kindle toolbar button and menu."""

from functools import partial

from qt.core import QAction, QToolButton

from calibre.gui2 import Dispatcher, error_dialog, question_dialog, warning_dialog
from calibre.gui2.actions import InterfaceAction

try:
    from calibre.utils.localization import _
except ImportError:  # older calibre only installs _ as a builtin
    pass

from calibre_plugins.send_to_kindle.config import email_accounts, prefs
from calibre_plugins.send_to_kindle.core.formats import SEND_FORMAT, has_send_format
from calibre_plugins.send_to_kindle.core.recipients import kindle_accounts, resolve_recipient


class SendToKindleAction(InterfaceAction):

    name = 'Send to Kindle'
    action_spec = (_('Send to Kindle'), None, _('Email the selected books to your Kindle'), None)
    popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    action_add_menu = True
    action_menu_clone_qaction = _('Send selected books to Kindle')
    action_type = 'current'
    dont_add_to = frozenset(['context-menu-device', 'toolbar-device', 'menubar-device'])

    def genesis(self):
        # get_icons is injected into plugin modules by calibre's plugin loader.
        icon = get_icons('images/icon.png', _('Send to Kindle'))
        self.qaction.setIcon(icon)
        self.menuless_qaction.setIcon(icon)
        self.qaction.triggered.connect(lambda checked=False: self.send_selected())
        menu = self.qaction.menu()
        # One "Send to <address>" entry per Kindle account goes above this
        # separator, rebuilt each time the menu opens.
        self.address_actions = []
        self.address_separator = menu.addSeparator()
        menu.aboutToShow.connect(self.rebuild_address_actions)
        self.create_menu_action(
            menu, 'send-to-kindle-customize', _('&Customize plugin') + '...',
            icon='config.png', shortcut=False, triggered=self.show_configuration)

    def rebuild_address_actions(self):
        """Refresh the per-address entries from calibre's current email accounts."""
        menu = self.qaction.menu()
        for ac in self.address_actions:
            menu.removeAction(ac)
            ac.deleteLater()
        self.address_actions = []
        for address in kindle_accounts(email_accounts()):
            ac = QAction(_('Send to %s') % address, menu)
            # triggered passes a checked flag, so it lands in the first parameter.
            ac.triggered.connect(lambda checked=False, address=address: self.send_selected(address))
            menu.insertAction(self.address_separator, ac)
            self.address_actions.append(ac)

    def location_selected(self, loc):
        self.qaction.setEnabled(loc == 'library')
        self.menuless_qaction.setEnabled(loc == 'library')

    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def selected_book_ids(self):
        view = self.gui.library_view
        rows = view.selectionModel().selectedRows()
        return [view.model().id(r) for r in rows]

    def send_selected(self, to=None):
        """Validate the setup, work out what to send, and start the jobs.

        ``to`` sends to that address instead of the one chosen in the settings.
        """
        book_ids = self.selected_book_ids()
        if not book_ids:
            return error_dialog(self.gui, _('No books selected'),
                                _('Select one or more books to send to your Kindle.'), show=True)

        accounts = email_accounts()
        if not accounts:
            if question_dialog(
                    self.gui, _('Email not set up'),
                    '<p>' + _('No email accounts are configured in calibre. Set up email, '
                              'including your Kindle address, in Preferences → '
                              'Sharing books by email.') + '</p><p>' + _('Open those preferences now?')):
                self.open_email_preferences()
            return

        if to is not None and to not in accounts:
            return error_dialog(
                self.gui, _('No Kindle address'),
                _("%s is no longer one of calibre's email accounts.") % to, show=True)
        if to is None:
            to = resolve_recipient(prefs['kindle_address'], accounts)
        if to is None:
            if prefs['kindle_address']:
                msg = _('The address %s chosen in the Send to Kindle settings is no longer one of '
                        "calibre's email accounts.") % prefs['kindle_address']
            else:
                msg = _("None of calibre's email accounts is a Kindle address "
                        '(ending in @kindle.com or @kindle.cn).')
            return error_dialog(
                self.gui, _('No Kindle address'),
                msg + ' ' + _('Add your Kindle address in Preferences → Sharing books by email, '
                              'or choose an address in this plugin\'s settings.'), show=True)

        from calibre_plugins.send_to_kindle.utils import SendItem, TemplateError, render_template

        db = self.gui.current_db.new_api
        template = prefs['template']
        items, skipped = [], []
        for book_id in book_ids:
            mi = db.get_metadata(book_id, get_cover=False)
            if not has_send_format(db.formats(book_id)):
                skipped.append(_('%(title)s (has %(fmts)s)') % dict(
                    title=mi.title, fmts=', '.join(db.formats(book_id)) or _('no formats')))
                continue
            try:
                rendered = render_template(template, mi)
            except TemplateError as err:
                return error_dialog(
                    self.gui, _('Template error'),
                    _('The attachment template failed for "%s". Fix it in the Send to Kindle settings.') % mi.title,
                    det_msg=str(err), show=True)
            items.append(SendItem(book_id, mi, SEND_FORMAT, rendered))

        if items:
            self.start_prepare_job(db, items, to)
        if skipped:
            warning_dialog(
                self.gui, _('Some books were not sent'),
                _('%(num)d book(s) have no %(fmt)s and were skipped. Convert them to %(fmt)s '
                  'first. Click "Show details" for the list.') % dict(num=len(skipped), fmt=SEND_FORMAT),
                det_msg='\n'.join(skipped), show=True)

    def start_prepare_job(self, db, items, to):
        from calibre.gui2.threaded_jobs import ThreadedJob
        from calibre_plugins.send_to_kindle.utils import prepare_files

        if len(items) == 1:
            desc = _('Prepare %s for Kindle') % items[0].title
        else:
            desc = _('Prepare %d books for Kindle') % len(items)
        job = ThreadedJob(
            'send_to_kindle', desc, prepare_files,
            (db, items, prefs['embed_metadata'], prefs['title_in_metadata']), {},
            Dispatcher(partial(self.files_prepared, to=to)))
        self.gui.job_manager.run_threaded_job(job)
        self.gui.status_bar.show_message(desc, 3000)

    def files_prepared(self, job, to=None):
        """Hand the prepared files to calibre's email jobs."""
        if job.failed:
            return self.gui.job_exception(job, dialog_title=_('Failed to prepare books for Kindle'))
        prepared, failed = job.result
        if prepared:
            from calibre.gui2.email import send_mails
            send_mails(
                [item.title for item, path in prepared],
                Dispatcher(partial(self.gui.email_sent, remove=[])),
                [path for item, path in prepared],
                [to] * len(prepared),
                [item.subject for item, path in prepared],
                [item.text for item, path in prepared],
                [item.filename for item, path in prepared],
                self.gui.job_manager)
            self.gui.status_bar.show_message(_('Sending email to') + ' ' + to, 3000)
        if failed:
            warning_dialog(
                self.gui, _('Some books were not sent'),
                _('%d book(s) could not be copied for sending. Click "Show details" for the errors.') % len(failed),
                det_msg='\n'.join('%s: %s' % (item.title, err) for item, err in failed), show=True)

    def open_email_preferences(self):
        try:
            self.gui.iactions['Preferences'].do_config(
                initial_plugin=('Sharing', 'Email'), close_after_initial=True)
        except Exception:
            import traceback
            traceback.print_exc()
