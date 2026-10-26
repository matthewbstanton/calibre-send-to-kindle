"""The Send to Kindle toolbar button and menu."""

from functools import partial

from qt.core import QToolButton

from calibre.gui2 import Dispatcher, error_dialog, question_dialog, warning_dialog
from calibre.gui2.actions import InterfaceAction

try:
    from calibre.utils.localization import _
except ImportError:  # older calibre only installs _ as a builtin
    pass

from calibre_plugins.send_to_kindle.config import email_accounts, prefs
from calibre_plugins.send_to_kindle.core.formats import choose_format, parse_format_list
from calibre_plugins.send_to_kindle.core.recipients import resolve_recipient


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
        self.qaction.triggered.connect(self.send_selected)
        menu = self.qaction.menu()
        menu.addSeparator()
        self.create_menu_action(
            menu, 'send-to-kindle-customize', _('&Customize plugin') + '...',
            icon='config.png', shortcut=False, triggered=self.show_configuration)

    def location_selected(self, loc):
        self.qaction.setEnabled(loc == 'library')
        self.menuless_qaction.setEnabled(loc == 'library')

    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def selected_book_ids(self):
        view = self.gui.library_view
        rows = view.selectionModel().selectedRows()
        return [view.model().id(r) for r in rows]

    def send_selected(self):
        """Validate the setup, work out what to send, and start the jobs."""
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
        formats = parse_format_list(prefs['formats'])
        template = prefs['template']
        items, skipped = [], []
        for book_id in book_ids:
            mi = db.get_metadata(book_id, get_cover=False)
            fmt = choose_format(db.formats(book_id), formats)
            if fmt is None:
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
            items.append(SendItem(book_id, mi, fmt, rendered))

        if items:
            self.start_prepare_job(db, items, to)
        if skipped:
            warning_dialog(
                self.gui, _('Some books were not sent'),
                _('%(num)d book(s) have none of the formats %(fmts)s and were skipped. '
                  'Click "Show details" for the list.') % dict(num=len(skipped), fmts=', '.join(formats)),
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
