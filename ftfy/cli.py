"""
A simple command-line utility for fixing text found in a file.

Because files do not come with their encoding marked, it first runs the file
through `ftfy.guess_bytes`, then runs it through `ftfy.fix_text`.
"""
from ftfy import fix_file, __version__

import sys
ENCODE_STDIO = (sys.hexversion < 0x03000000)


ENCODE_ERROR_TEXT = """
Unfortunately, this output stream does not support Unicode.

- If this is a Linux system, your locale may be very old or misconfigured.
  You should `export LANG=C.UTF-8`.
- If this is a Windows system, please do not use the Command Prompt (cmd.exe)
  to run Python. It does not and cannot support real Unicode.
"""

DECODE_ERROR_TEXT = """
Error: this input couldn't be decoded as %r. We got the following error:

    %s

ftfy works best when its input is in a known encoding. You can use `ftfy -g`
to guess, if you're desperate. Otherwise, give the encoding name with the
`-e` option, such as `ftfy -e latin-1`.
"""


def main():
    """
    Run ftfy as a command-line utility. (Requires Python 2.7 or later, or
    the 'argparse' module.)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="ftfy (fixes text for you), version %s" % __version__
    )
    parser.add_argument('filename', default='-', nargs='?',
                        help='The file whose Unicode is to be fixed. Defaults '
                             'to -, meaning standard input.')
    parser.add_argument('-g', '--guess', action='store_true',
                        help="Ask ftfy to guess the encoding of your input. "
                             "This is risky. Overrides -e.")
    parser.add_argument('-e', '--encoding', type=str, default='utf-8',
                        help='The encoding of the input. Defaults to UTF-8.')
    parser.add_argument('-n', '--normalization', type=str, default='NFC',
                        help='The normalization of Unicode to apply. '
                             'Defaults to NFC. Can be "none".')
    parser.add_argument('--preserve-entities', action='store_true',
                        help="Leave HTML entities as they are. The default "
                             "is to decode them in non-HTML files.")

    args = parser.parse_args()

    encoding = args.encoding
    if args.guess:
        encoding = None
        file_flags = 'rb'
    else:
        file_flags = 'r'

    if args.filename == '-':
        file = sys.stdin
    else:
        file = open(args.filename, file_flags)

    normalization = args.normalization
    if normalization.lower() == 'none':
        normalization = None

    if args.preserve_entities:
        fix_entities = False
    else:
        fix_entities = 'auto'

    try:
        for line in fix_file(file, encoding=encoding,
                             fix_entities=fix_entities,
                             normalization=normalization):
            if ENCODE_STDIO:
                sys.stdout.write(line.encode('utf-8'))
            else:
                try:
                    sys.stdout.write(line)
                except UnicodeEncodeError:
                    sys.stderr.write(ENCODE_ERROR_TEXT)
                    sys.exit(1)
    except UnicodeDecodeError as err:
        sys.stderr.write(DECODE_ERROR_TEXT % (encoding, err))
        sys.exit(1)


if __name__ == '__main__':
    main()
