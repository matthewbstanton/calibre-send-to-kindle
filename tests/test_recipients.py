import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recipients import is_kindle_address, kindle_accounts, resolve_recipient  # noqa: E402


class TestIsKindleAddress(unittest.TestCase):

    def test_kindle_domains(self):
        for addr in ('me@kindle.com', 'me@free.kindle.com', 'ME@Kindle.CN', 'me@free.kindle.cn'):
            self.assertTrue(is_kindle_address(addr), addr)

    def test_other_domains(self):
        for addr in ('me@gmail.com', 'kindle.com@example.org', 'me@notkindle.com', '', None):
            self.assertFalse(is_kindle_address(addr), addr)

    def test_lists_and_display_names(self):
        self.assertTrue(is_kindle_address('me@example.org, me@kindle.com'))
        self.assertTrue(is_kindle_address('My Kindle <me@kindle.com>'))


class TestResolveRecipient(unittest.TestCase):

    def accounts(self):
        # Calibre's format: address -> [formats, auto_send, is_default]
        return {
            'me@example.org': ['EPUB', False, True],
            'old@kindle.com': ['EPUB', False, False],
            'new@kindle.com': ['EPUB', False, True],
        }

    def test_kindle_accounts_prefers_default(self):
        self.assertEqual(kindle_accounts(self.accounts()), ['new@kindle.com', 'old@kindle.com'])

    def test_automatic_picks_kindle(self):
        accounts = self.accounts()
        accounts['new@kindle.com'][2] = False
        self.assertEqual(resolve_recipient('', accounts), 'old@kindle.com')

    def test_automatic_prefers_default_kindle(self):
        self.assertEqual(resolve_recipient('', self.accounts()), 'new@kindle.com')

    def test_configured_address_used(self):
        self.assertEqual(resolve_recipient('me@example.org', self.accounts()), 'me@example.org')

    def test_configured_address_missing(self):
        self.assertIsNone(resolve_recipient('gone@kindle.com', self.accounts()))

    def test_no_kindle_accounts(self):
        self.assertIsNone(resolve_recipient('', {'me@example.org': ['EPUB', False, True]}))
        self.assertIsNone(resolve_recipient('', {}))
        self.assertIsNone(resolve_recipient(None, None))

    def test_malformed_account_value(self):
        self.assertEqual(resolve_recipient('', {'a@kindle.com': None}), 'a@kindle.com')


if __name__ == '__main__':
    unittest.main()
