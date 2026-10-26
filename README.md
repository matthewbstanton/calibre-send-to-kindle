# Send to Kindle (Calibre plugin)

A calibre toolbar button that emails the selected books to your Kindle's
Send-to-Kindle address.

Calibre can already do this with **Connect/share → Email to**. This plugin
renames what it sends. Each attachment is named from a calibre template, and
by default the same name goes into the book's embedded title. Books in a series
then show up and sort in reading order on the Kindle:

```
Foundation [01] - Foundation.epub
Foundation [02] - Foundation and Empire.epub
Foundation [03] - Second Foundation.epub
```

Your library is never changed. Only the temporary copy that is sent gets
renamed and has its metadata updated.

## Requirements

- calibre 7.0 or later.
- Email set up in calibre: **Preferences → Sharing books by email**. Add your
  Kindle address (`…@kindle.com`), and add your sending address to your
  Amazon account's *Approved Personal Document E-mail List*. The plugin uses
  calibre's SMTP settings and stores no mail credentials of its own.

## Use

1. Select one or more books in the library.
2. Click **Send to Kindle**, or choose **Send selected books to Kindle** from
   the button's menu.

For each book the plugin:

1. Picks the first format from your preferred list that the book has.
2. Evaluates the attachment template for the book.
3. Copies that format to a temporary file with the new name. By default it
   also writes the library metadata and cover into the copy, with the rendered
   template as the title.
4. Sends the file with calibre's own email jobs.

Steps 3 and 4 run as background jobs, which you can follow in calibre's Jobs
list. If sending fails, calibre's usual error dialog appears, with the log.

### What happens when something is missing

- **No books selected:** you get an error and nothing is sent.
- **No email accounts in calibre:** the plugin offers to open
  Preferences → Sharing books by email.
- **No Kindle address:** you get an error asking you to add one in calibre's
  email preferences or to pick an address in the plugin settings. This also
  happens when the address chosen in the settings has been removed from
  calibre.
- **A book has none of the preferred formats:** the other books are still
  sent, and a warning lists each skipped book along with the formats it does
  have. The plugin doesn't convert books. Use calibre's Convert first.
- **A template error:** nothing is sent, and the error is shown so you can
  fix the template.
- **Embedding metadata fails** (for example, a PDF calibre can't write to):
  the file is sent unchanged, and the problem is recorded in the job log.

## Settings

Open them from **Preferences → Plugins → Send to Kindle → Customize plugin**,
or from **Customize plugin…** in the button's menu.

| Setting | Default | Meaning |
|---|---|---|
| Send to | Automatic | One of calibre's email accounts. *Automatic* uses the first account at a Kindle domain (`kindle.com`, `free.kindle.com`, `kindle.cn`, `free.kindle.cn`), preferring the one marked as calibre's default. |
| Formats, in order of preference | `EPUB, AZW3, MOBI, PDF` | The first format the book has is sent. |
| Attachment template | `{series:\|\| }{series_index:0>2s\|[\|] - }{title}` | A calibre template, with the full template language. **Edit…** opens calibre's template editor, and **Reset** restores the default. |
| Update the metadata inside the sent file from the library | On | Writes the library metadata and cover into the copy that is sent, like calibre's own email does. |
| Use the rendered template as the title inside the sent file | On | Sets the embedded title (and title sort) of the sent copy to the rendered template. This only applies when the previous option is on. |

### The default template

`{series:|| }{series_index:0>2s|[|] - }{title}` gives:

- `Foundation [02] - Foundation and Empire` for book 2 of *Foundation*.
- `Foundation [2.5] - Some Novella` for a fractional series index.
- `Foundation and Empire` for a book with no series. The plugin empties the
  series index of a book that has no series, so you don't get a stray
  `[01] - `.

### Filenames

The template's output is cleaned up before it's used as a filename:

- Characters that aren't allowed in filenames (`< > : " / \ | ? *` and
  control characters) become spaces.
- Runs of whitespace collapse to one space.
- Leading and trailing dots and spaces are removed.
- The name is cut to 120 characters.
- Windows reserved names such as `CON` get a trailing `_`.
- If nothing is left, the book's title is used, and failing that, `book`.

The embedded title isn't cleaned this way, so `Dune [02] - Dune: Messiah`
keeps its colon inside the book even though the file is named
`Dune [02] - Dune Messiah.epub`.

### Why the embedded title is on by default

For an EPUB, Amazon's Send-to-Kindle service usually takes the title from the
metadata inside the file, not from the attachment's name. Renaming the file
alone wouldn't change what the Kindle library shows or how it sorts. calibre's
own email code notes that Amazon sometimes reads the attachment name instead.
So the plugin puts the rendered template in both places, and the result is the
same whichever one Amazon uses. Turn the option off if you want the Kindle to
show the book's real title and only want the files renamed.

### Notes on formats

Amazon's Send-to-Kindle service accepts EPUB and PDF, among others. It no
longer accepts MOBI or AZW3 by email, and it replies with a rejection message
if you send them. They stay in the default list as a fallback for other
addresses and older devices. Remove them if you only send to Amazon.

Calibre's email code also replaces the subject and body of mail sent to Kindle
addresses with random English text, because Amazon's service can't handle
non-ASCII text there. The attachment name is kept as it is.

## Development

- `core/` holds the pure logic: filename cleaning, format choice and recipient
  choice. It has no calibre or Qt imports and is unit-tested.
- `action.py`, `config.py` and `utils.py` run inside calibre.

```
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 build.py            # writes send_to_kindle.zip
python3 build.py --install  # also runs calibre-customize -a send_to_kindle.zip
```

Every file that ships must be listed in `INCLUDES` in `build.py`.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
