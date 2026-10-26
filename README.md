# Send to Kindle (Calibre plugin)

A calibre toolbar button that emails the selected books to your Kindle's
Send-to-Kindle address, named so that series stay in reading order.

> **Email is set up in calibre, not in this plugin.** Your SMTP server, your
> sending address and your Kindle address all live in calibre's built-in
> **Preferences → Sharing books by email**, the same place calibre's own
> *Email to* uses. The plugin reads them from there and has no mail settings of
> its own. If calibre can already email books, the plugin works with no extra
> setup.

## Why this matters

Your Kindle library sorts books by the name they arrive with. If you send a
series with calibre's built-in **Connect/share → Email to**, each book arrives
under its own title. The books then sort alphabetically, scattered through
your library and out of reading order:

```
Oathbringer
The Way of Kings
Words of Radiance
```

This plugin names each book it sends from a calibre template that puts the
series and its number first. Books in a series then group together and sort
in reading order:

```
The Stormlight Archive [01] - The Way of Kings.epub
The Stormlight Archive [02] - Words of Radiance.epub
The Stormlight Archive [03] - Oathbringer.epub
```

The more series you read, the more this matters. Without it, finding the next
book means remembering its title. With it, the next book sits right after the
one you just finished.

Amazon takes a book's name from the attachment filename or from the title
embedded in the EPUB, depending on the file. So by default the plugin puts the
same name in both places, and the order holds whichever one Amazon uses.

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
   the button's menu. Both send to the address in the plugin settings.

To send to a different Kindle, open the button's menu and pick
**Send to <address>**. The menu has one entry for each calibre email account
at a Kindle domain, and it updates whenever you change calibre's email
preferences.

For each book the plugin:

1. Checks that the book has an EPUB. Only EPUB is sent.
2. Evaluates the attachment template for the book.
3. Copies the EPUB to a temporary file with the new name. By default it
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
- **A book has no EPUB:** the other books are still sent, and a warning lists
  each skipped book along with the formats it does have. The plugin doesn't
  convert books. Use calibre's Convert to make an EPUB first.
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

The plugin only sends EPUB. Amazon's Send-to-Kindle service no longer accepts
MOBI or AZW3 by email and replies with a rejection message if you send them.
It does accept some other formats, such as PDF, but EPUB is the one whose
embedded title the plugin can set reliably. To send another format, use
calibre's own **Connect/share → Email to**.

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
