"""Send to Kindle: email selected books to a Kindle with series-aware names."""

from calibre.customize import InterfaceActionBase


class SendToKindlePlugin(InterfaceActionBase):

    name = 'Send to Kindle'
    description = ('Email the selected books to your Kindle, naming each attachment '
                   'with a template so series books show and sort in order.')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Matthew Stanton'
    version = (1, 0, 0)
    # 7.0 keeps the attachment name for Kindle addresses in send_mails and
    # ships Qt 6 with the qt.core namespace.
    minimum_calibre_version = (7, 0, 0)

    actual_plugin = 'calibre_plugins.send_to_kindle.action:SendToKindleAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.send_to_kindle.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
