"""Decide whether a book can be sent."""

#: The only format sent. Amazon's Send-to-Kindle no longer accepts MOBI or
#: AZW3 by email, and EPUB is the format it handles best.
SEND_FORMAT = 'EPUB'


def has_send_format(available):
    """True if ``available``, an iterable of format names, includes EPUB.

    The comparison ignores case and surrounding whitespace.
    """
    return any((f or '').strip().upper() == SEND_FORMAT for f in available or ())
