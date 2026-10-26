import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.formats import SEND_FORMAT, has_send_format  # noqa: E402


class TestHasSendFormat(unittest.TestCase):

    def test_send_format_is_epub(self):
        self.assertEqual(SEND_FORMAT, 'EPUB')

    def test_epub_among_others(self):
        self.assertTrue(has_send_format(('PDF', 'EPUB', 'MOBI')))

    def test_case_and_whitespace_insensitive(self):
        self.assertTrue(has_send_format(['epub']))
        self.assertTrue(has_send_format([' Epub ']))

    def test_no_epub(self):
        self.assertFalse(has_send_format(('PDF', 'MOBI', 'AZW3')))
        self.assertFalse(has_send_format(('KEPUB',)))
        self.assertFalse(has_send_format(()))
        self.assertFalse(has_send_format(None))
        self.assertFalse(has_send_format([None, '']))


if __name__ == '__main__':
    unittest.main()
