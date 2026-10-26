import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.formats import (  # noqa: E402
    DEFAULT_FORMAT_ORDER, choose_format, format_list_to_text, parse_format_list,
)


class TestParseFormatList(unittest.TestCase):

    def test_default_order_starts_with_epub(self):
        self.assertEqual(DEFAULT_FORMAT_ORDER[0], 'EPUB')

    def test_parse(self):
        self.assertEqual(parse_format_list('epub, azw3,mobi  pdf'), ('EPUB', 'AZW3', 'MOBI', 'PDF'))

    def test_dots_semicolons_and_duplicates(self):
        self.assertEqual(parse_format_list('.epub; EPUB ;.Pdf'), ('EPUB', 'PDF'))

    def test_empty(self):
        self.assertEqual(parse_format_list(''), ())
        self.assertEqual(parse_format_list(None), ())
        self.assertEqual(parse_format_list(' , ;'), ())

    def test_round_trip(self):
        text = format_list_to_text(DEFAULT_FORMAT_ORDER)
        self.assertEqual(text, 'EPUB, AZW3, MOBI, PDF')
        self.assertEqual(parse_format_list(text), DEFAULT_FORMAT_ORDER)


class TestChooseFormat(unittest.TestCase):

    def test_first_preferred_wins(self):
        self.assertEqual(choose_format(('PDF', 'EPUB', 'MOBI'), DEFAULT_FORMAT_ORDER), 'EPUB')

    def test_fallback(self):
        self.assertEqual(choose_format(('PDF', 'MOBI'), DEFAULT_FORMAT_ORDER), 'MOBI')
        self.assertEqual(choose_format(('PDF', 'TXT'), DEFAULT_FORMAT_ORDER), 'PDF')

    def test_case_insensitive(self):
        self.assertEqual(choose_format(['epub'], ['Epub']), 'EPUB')

    def test_none_acceptable(self):
        self.assertIsNone(choose_format(('CBZ', 'TXT'), DEFAULT_FORMAT_ORDER))
        self.assertIsNone(choose_format((), DEFAULT_FORMAT_ORDER))
        self.assertIsNone(choose_format(None, DEFAULT_FORMAT_ORDER))
        self.assertIsNone(choose_format(('EPUB',), ()))


if __name__ == '__main__':
    unittest.main()
