"""Turn a rendered attachment template into a safe filename and title."""

import re

#: Default attachment template: "Series [02] - Title" for books in a series,
#: plain "Title" otherwise.
DEFAULT_TEMPLATE = '{series:|| }{series_index:0>2s|[|] - }{title}'

#: Longest filename stem (without extension) we produce. Long enough for any
#: sensible title, short enough to stay well under every filesystem limit and
#: avoid mail clients splitting the attachment name over several header lines.
MAX_STEM_LENGTH = 120

#: Used when both the rendered template and the title are empty.
FALLBACK_STEM = 'book'

# Characters that are illegal in filenames on at least one of Windows, macOS
# or Linux, plus every ASCII control character.
_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_WHITESPACE = re.compile(r'\s+')
_WINDOWS_RESERVED = frozenset(
    ['CON', 'PRN', 'AUX', 'NUL']
    + ['COM%d' % i for i in range(1, 10)]
    + ['LPT%d' % i for i in range(1, 10)]
)


def collapse_whitespace(text):
    """Replace every run of whitespace with one space and trim both ends."""
    return _WHITESPACE.sub(' ', text or '').strip()


def sanitize_filename_stem(text, max_length=MAX_STEM_LENGTH):
    """Return ``text`` made safe to use as a filename without its extension.

    Illegal characters become spaces, whitespace is collapsed, leading and
    trailing dots and spaces are removed, and the result is cut to at most
    ``max_length`` characters. May return an empty string.
    """
    stem = collapse_whitespace(_ILLEGAL_CHARS.sub(' ', text or ''))
    stem = stem.strip(' .')
    if len(stem) > max_length:
        stem = stem[:max_length].rstrip(' .')
    if stem.split('.')[0].upper() in _WINDOWS_RESERVED:
        stem = stem + '_'
    return stem


def attachment_filename(rendered, title, fmt, max_length=MAX_STEM_LENGTH):
    """Return the attachment filename for a book.

    ``rendered`` is the evaluated template, ``title`` the book's own title
    (the fallback when the rendered value sanitises to nothing) and ``fmt``
    the format being sent, such as ``'EPUB'``.
    """
    stem = (
        sanitize_filename_stem(rendered, max_length)
        or sanitize_filename_stem(title, max_length)
        or FALLBACK_STEM
    )
    ext = (fmt or '').strip().lstrip('.').lower()
    return stem + '.' + ext if ext else stem


def display_title(rendered, title):
    """Return the title to embed in the sent file's metadata.

    Unlike the filename this keeps characters such as ``:`` and ``?``; it only
    collapses whitespace, and falls back to ``title`` when the rendered value
    is empty.
    """
    return collapse_whitespace(rendered) or collapse_whitespace(title) or FALLBACK_STEM
