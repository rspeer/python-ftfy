"""
A simple command-line utility for fixing text found in a file.

This utility knows nothing about the initial encoding of the file, so it will
guess Latin-1 and then try to fix it in the very likely event that that guess
is wrong.

That behavior is slower than strictly necessary, and possibly a bit risky,
so consider this utility a proof of concept.
"""
from ftfy import fix_file

import sys
ENCODE_STDOUT = (sys.hexversion < 0x03000000)


def main():
    """
    Run ftfy as a command-line utility. (Requires Python 2.7 or later, or
    the 'argparse' module.)
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='file to transcode')

    args = parser.parse_args()

    file = open(args.filename)
    for line in fix_file(file):
        if ENCODE_STDOUT:
            sys.stdout.write(line.encode('utf-8'))
        else:
            sys.stdout.write(line)


if __name__ == '__main__':
    main()
