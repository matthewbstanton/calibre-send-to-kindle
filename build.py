#!/usr/bin/env python3
"""Build the plugin zip.

    python3 build.py            # writes send_to_kindle.zip
    python3 build.py --install  # also installs it with calibre-customize
"""

import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP_NAME = 'send_to_kindle.zip'

#: Every file that ships in the plugin zip, relative to the repo root.
INCLUDES = [
    '__init__.py',
    'action.py',
    'config.py',
    'utils.py',
    'core/__init__.py',
    'core/filenames.py',
    'core/formats.py',
    'core/recipients.py',
    'images/icon.png',
    'plugin-import-name-send_to_kindle.txt',
    'README.md',
    'LICENSE',
]


def build():
    missing = [p for p in INCLUDES if not os.path.isfile(os.path.join(HERE, p))]
    if missing:
        sys.exit('Missing files listed in INCLUDES: ' + ', '.join(missing))
    out = os.path.join(HERE, ZIP_NAME)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel in INCLUDES:
            zf.write(os.path.join(HERE, rel), rel)
    print('Built', out)
    return out


def main():
    out = build()
    if '--install' in sys.argv[1:]:
        subprocess.check_call(['calibre-customize', '-a', out])


if __name__ == '__main__':
    main()
