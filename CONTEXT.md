# Glossary

- **Kindle address**: an address at one of Amazon's Send-to-Kindle domains
  (`kindle.com`, `free.kindle.com`, `kindle.cn`, `free.kindle.cn`). Mail sent
  there is delivered to the user's Kindle library.
- **Email account**: an entry in calibre's *Preferences → Sharing books by
  email* list. It's stored in calibre's `smtp` config as
  `accounts[address] = [formats, auto_send, is_default]`. The plugin only
  reads these and never stores SMTP settings of its own.
- **Attachment template**: the calibre template that's evaluated for each
  book to name what's sent.
- **Rendered title**: the attachment template's output for one book, with its
  whitespace collapsed. It can go into the sent file's embedded metadata.
- **Attachment filename**: the rendered title made safe for filenames, plus
  the format's extension.
- **Send format**: EPUB, the only format the plugin sends. It isn't
  configurable.
- **Skipped book**: a selected book that has no EPUB. It isn't sent, and it's
  listed in a warning.
- **Prepare job**: the background job that copies each book's format to a
  temp file named with its attachment filename and updates the copy's
  metadata. When it finishes, calibre's email jobs send the files.
