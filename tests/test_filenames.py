import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.filenames import (  # noqa: E402
    FALLBACK_STEM, MAX_STEM_LENGTH, attachment_filename, collapse_whitespace,
    display_title, sanitize_filename_stem,
)


class TestSanitizeFilenameStem(unittest.TestCase):

    def test_plain_text_unchanged(self):
        self.assertEqual(sanitize_filename_stem('Foundation [01] - Foundation'), 'Foundation [01] - Foundation')

    def test_illegal_characters_become_spaces(self):
        self.assertEqual(sanitize_filename_stem('Dune: Messiah?'), 'Dune Messiah')
        self.assertEqual(sanitize_filename_stem('AC/DC <live> "x" a\\b|c*'), 'AC DC live x a b c')

    def test_control_characters_removed(self):
        self.assertEqual(sanitize_filename_stem('a\x00b\x1fc\x7fd'), 'a b c d')

    def test_whitespace_collapsed(self):
        self.assertEqual(sanitize_filename_stem('  a \t\n  b  '), 'a b')

    def test_leading_and_trailing_dots_removed(self):
        self.assertEqual(sanitize_filename_stem('...hidden...'), 'hidden')

    def test_length_trimmed(self):
        stem = sanitize_filename_stem('x' * 500)
        self.assertEqual(len(stem), MAX_STEM_LENGTH)
        self.assertEqual(sanitize_filename_stem('abcdef', max_length=3), 'abc')

    def test_trim_does_not_leave_trailing_space_or_dot(self):
        self.assertEqual(sanitize_filename_stem('abc. def', max_length=5), 'abc')

    def test_unicode_kept(self):
        self.assertEqual(sanitize_filename_stem('Les Misérables — Tome 1'), 'Les Misérables — Tome 1')

    def test_windows_reserved_names(self):
        self.assertEqual(sanitize_filename_stem('con'), 'con_')
        self.assertEqual(sanitize_filename_stem('LPT1'), 'LPT1_')
        self.assertEqual(sanitize_filename_stem('Contact'), 'Contact')

    def test_empty(self):
        self.assertEqual(sanitize_filename_stem(''), '')
        self.assertEqual(sanitize_filename_stem(None), '')
        self.assertEqual(sanitize_filename_stem(' ?*: '), '')


class TestAttachmentFilename(unittest.TestCase):

    def test_series_name(self):
        self.assertEqual(
            attachment_filename('Foundation [02] - Foundation and Empire', 'Foundation and Empire', 'EPUB'),
            'Foundation [02] - Foundation and Empire.epub')

    def test_extension_normalised(self):
        self.assertEqual(attachment_filename('Title', 'Title', '.AZW3'), 'Title.azw3')

    def test_falls_back_to_title(self):
        self.assertEqual(attachment_filename('', 'The Title', 'pdf'), 'The Title.pdf')
        self.assertEqual(attachment_filename(' :?/ ', 'The: Title', 'pdf'), 'The Title.pdf')

    def test_falls_back_to_constant(self):
        self.assertEqual(attachment_filename('', '', 'epub'), FALLBACK_STEM + '.epub')

    def test_long_name_keeps_extension(self):
        name = attachment_filename('y' * 400, 't', 'epub')
        self.assertTrue(name.endswith('.epub'))
        self.assertEqual(len(name), MAX_STEM_LENGTH + len('.epub'))


class TestDisplayTitle(unittest.TestCase):

    def test_keeps_punctuation(self):
        self.assertEqual(display_title('Dune [02] - Dune: Messiah', 'Dune Messiah'), 'Dune [02] - Dune: Messiah')

    def test_collapses_whitespace(self):
        self.assertEqual(display_title('  a\n\n b ', 'x'), 'a b')

    def test_fallbacks(self):
        self.assertEqual(display_title('   ', 'Title'), 'Title')
        self.assertEqual(display_title('', ''), FALLBACK_STEM)

    def test_collapse_whitespace_none(self):
        self.assertEqual(collapse_whitespace(None), '')


if __name__ == '__main__':
    unittest.main()
