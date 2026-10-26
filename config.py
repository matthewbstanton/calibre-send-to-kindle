"""Plugin preferences and the configuration widget."""

from qt.core import (
    QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from calibre.gui2 import error_dialog
from calibre.utils.config import JSONConfig

try:
    from calibre.utils.localization import _
except ImportError:  # older calibre only installs _ as a builtin
    pass

from calibre_plugins.send_to_kindle.core.filenames import DEFAULT_TEMPLATE
from calibre_plugins.send_to_kindle.core.recipients import is_kindle_address, kindle_accounts

#: Stored in calibre's config directory as plugins/send_to_kindle.json.
prefs = JSONConfig('plugins/send_to_kindle')

#: Address to send to. Empty means "the first Kindle address in calibre's
#: email settings".
prefs.defaults['kindle_address'] = ''
#: Calibre template for the attachment filename (and embedded title).
prefs.defaults['template'] = DEFAULT_TEMPLATE
#: Write the library's metadata into the copy that is sent.
prefs.defaults['embed_metadata'] = True
#: When embedding metadata, use the rendered template as the title.
prefs.defaults['title_in_metadata'] = True


def email_accounts():
    """Return calibre's configured email accounts dict."""
    from calibre.utils.smtp import config as email_config
    return email_config().parse().accounts or {}


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = l = QVBoxLayout(self)
        form = QFormLayout()
        l.addLayout(form)

        self.address = QComboBox(self)
        self.address.setToolTip(
            _('Calibre email account to send to. Add or change accounts in '
              'Preferences → Sharing books by email.'))
        accounts = email_accounts()
        auto = kindle_accounts(accounts)
        auto_text = (_('Automatic (currently %s)') % auto[0]) if auto else _('Automatic (no Kindle address found)')
        self.address.addItem(auto_text, '')
        for addr in accounts:
            label = addr + ('  [Kindle]' if is_kindle_address(addr) else '')
            self.address.addItem(label, addr)
        current = prefs['kindle_address']
        if current and current not in accounts:
            self.address.addItem(_('%s (no longer configured)') % current, current)
        idx = self.address.findData(current)
        self.address.setCurrentIndex(max(idx, 0))
        form.addRow(_('&Send to:'), self.address)

        self.template = QLineEdit(self)
        self.template.setText(prefs['template'])
        self.template.setToolTip(
            _('Calibre template used to name the attachment. The full '
              'template language is available.'))
        tl = QHBoxLayout()
        tl.addWidget(self.template)
        self.edit_template_button = b = QPushButton(_('&Edit...'), self)
        b.clicked.connect(self.edit_template)
        tl.addWidget(b)
        self.reset_template_button = b = QPushButton(_('&Reset'), self)
        b.setToolTip(_('Restore the default template:') + ' ' + DEFAULT_TEMPLATE)
        b.clicked.connect(lambda: self.template.setText(DEFAULT_TEMPLATE))
        tl.addWidget(b)
        form.addRow(_('Attachment &template:'), tl)

        self.embed_metadata = QCheckBox(_('&Update the metadata inside the sent file from the library'), self)
        self.embed_metadata.setChecked(bool(prefs['embed_metadata']))
        l.addWidget(self.embed_metadata)
        self.title_in_metadata = QCheckBox(_('Use the rendered template as the &title inside the sent file'), self)
        self.title_in_metadata.setToolTip(
            _('Send-to-Kindle normally takes the title from the metadata '
              'inside an EPUB, not from the attachment filename. With this on, '
              'both carry the rendered template, so series books show and '
              'sort as "Series [01] - Title" on the device.'))
        self.title_in_metadata.setChecked(bool(prefs['title_in_metadata']))
        self.embed_metadata.toggled.connect(self.title_in_metadata.setEnabled)
        self.title_in_metadata.setEnabled(self.embed_metadata.isChecked())
        l.addWidget(self.title_in_metadata)

        note = QLabel(
            _('Mail is sent with the SMTP settings from Preferences → '
              'Sharing books by email. The copy in your library is never changed.'), self)
        note.setWordWrap(True)
        l.addWidget(note)
        l.addStretch(1)

    def edit_template(self):
        from calibre.gui2.dialogs.template_dialog import TemplateDialog
        d = TemplateDialog(self, self.template.text())
        if d.exec():
            self.template.setText(d.rule[1])

    def validate(self):
        """Check the settings; show an error and return False if invalid."""
        template = self.template.text().strip()
        if not template:
            error_dialog(self, _('No template'), _('The attachment template cannot be empty.'), show=True)
            return False
        from calibre.utils.formatter import validation_formatter
        try:
            validation_formatter.validate(template)
        except Exception as err:
            error_dialog(self, _('Invalid template'), _('The attachment template is invalid:') + '\n' + str(err), show=True)
            return False
        return True

    def save_settings(self):
        prefs['kindle_address'] = self.address.currentData() or ''
        prefs['template'] = self.template.text().strip()
        prefs['embed_metadata'] = self.embed_metadata.isChecked()
        prefs['title_in_metadata'] = self.title_in_metadata.isChecked()
