"""Calibre-side helpers: template rendering and preparing the files to send."""

import os

try:
    from calibre.utils.localization import _
except ImportError:  # older calibre only installs _ as a builtin
    pass

from calibre_plugins.send_to_kindle.core.filenames import attachment_filename, display_title

# Prefix safe_format puts on its result when the template fails.
_TEMPLATE_ERROR = '\x00SEND_TO_KINDLE_TEMPLATE_ERROR'


class TemplateError(ValueError):
    pass


def render_template(template, mi):
    """Evaluate ``template`` against the Metadata ``mi`` with calibre's engine.

    A book without a series gets an empty ``series_index``, so templates like
    the default one do not produce "[01] - " for standalone books. Raises
    :class:`TemplateError` if the template fails. Call from the GUI thread.
    """
    from calibre.ebooks.metadata.book.formatter import SafeFormat
    mi = mi.deepcopy_metadata()
    if not mi.series:
        mi.series_index = None
    ans = SafeFormat().safe_format(template, mi, _TEMPLATE_ERROR, mi)
    if ans.startswith(_TEMPLATE_ERROR):
        raise TemplateError(ans[len(_TEMPLATE_ERROR):].strip())
    return ans


class SendItem:
    """One book to send: what to copy, what to call it and what to embed."""

    def __init__(self, book_id, mi, fmt, rendered):
        self.book_id = book_id
        self.mi = mi
        self.fmt = fmt
        self.title = mi.title or _('Unknown')
        self.filename = attachment_filename(rendered, self.title, fmt)
        self.embedded_title = display_title(rendered, self.title)

    @property
    def subject(self):
        return _('E-book:') + ' ' + self.embedded_title

    @property
    def text(self):
        from calibre.ebooks.metadata import authors_to_string
        authors = authors_to_string(self.mi.authors or [_('Unknown')])
        return '%s\n\n%s\n\t%s %s\n\n%s' % (
            _('Attached, you will find the e-book'), self.title, _('by'), authors,
            _('in the %s format.') % self.fmt)


def prepare_files(db, items, embed_metadata, title_in_metadata, log=None, abort=None, notifications=None):
    """ThreadedJob function: copy each book's format into a temp file.

    Each file is named with the item's rendered filename, inside its own temp
    directory so that duplicate names cannot collide. If ``embed_metadata`` is
    set, the library metadata (and cover) is written into the copy, with the
    rendered title if ``title_in_metadata`` is set. Returns ``(prepared,
    failed)``: a list of ``(item, path)`` and a list of ``(item, error)``.
    """
    from calibre.ebooks.metadata.meta import set_metadata
    from calibre.ptempfile import PersistentTemporaryDirectory

    prepared, failed = [], []
    for i, item in enumerate(items):
        if abort is not None and abort.is_set():
            break
        if notifications is not None:
            notifications.put((i / len(items), item.title))
        try:
            tdir = PersistentTemporaryDirectory('_send_to_kindle')
            path = os.path.join(tdir, item.filename)
            with open(path, 'w+b') as f:
                db.copy_format_to(item.book_id, item.fmt, f)
                if embed_metadata:
                    mi = item.mi.deepcopy_metadata()
                    cdata = db.cover(item.book_id)
                    if cdata:
                        mi.cover_data = ('jpeg', cdata)
                    if title_in_metadata:
                        mi.title = mi.title_sort = item.embedded_title
                    try:
                        f.seek(0)
                        set_metadata(f, mi, item.fmt.lower())
                    except Exception:
                        # Sending the file untouched beats not sending it.
                        if log is not None:
                            log.exception('Failed to set metadata in %s, sending it unchanged' % item.filename)
            if log is not None:
                log('Prepared %s as %s' % (item.title, path))
            prepared.append((item, path))
        except Exception as err:
            if log is not None:
                log.exception('Failed to prepare %s' % item.title)
            failed.append((item, str(err)))
    if notifications is not None:
        notifications.put((1.0, _('Done')))
    return prepared, failed
