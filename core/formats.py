"""Choose which of a book's formats to send."""

import re

#: Send-to-Kindle accepts EPUB, so it comes first; the rest are fallbacks.
DEFAULT_FORMAT_ORDER = ('EPUB', 'AZW3', 'MOBI', 'PDF')

_SEPARATORS = re.compile(r'[\s,;]+')


def parse_format_list(text):
    """Parse a user-entered list such as ``"epub, .pdf mobi"``.

    Returns a tuple of upper-case format names in the given order, with
    duplicates and leading dots removed.
    """
    ans = []
    for part in _SEPARATORS.split(text or ''):
        fmt = part.strip().lstrip('.').upper()
        if fmt and fmt not in ans:
            ans.append(fmt)
    return tuple(ans)


def format_list_to_text(formats):
    """Inverse of :func:`parse_format_list`, for showing in the settings."""
    return ', '.join(formats)


def choose_format(available, preferred):
    """Return the first format in ``preferred`` that is in ``available``.

    Both are iterables of format names; the comparison ignores case. Returns
    the upper-case format name, or None when no preferred format is present.
    """
    have = {(f or '').strip().upper() for f in available or ()}
    for fmt in preferred:
        fmt = (fmt or '').strip().upper()
        if fmt and fmt in have:
            return fmt
    return None
