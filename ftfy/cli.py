from ftfy import fix_file
import codecs

import sys
ENCODE_STDOUT = (sys.version_info.major < 3)


def main():
    """
    Run ftfy as a command-line utility. (Requires Python 2.7 or later, or
    the 'argparse' module.)
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='file to transcode')

    args = parser.parse_args()

    # Why open in Latin-1? Because it'll never make anything worse, and
    # we're about to make things better.
    file = codecs.open(args.filename, encoding='latin-1')
    for line in fix_file(file):
        if ENCODE_STDOUT:
            sys.stdout.write(line.encode('utf-8'))
        else:
            sys.stdout.write(line)


if __name__ == '__main__':
    main()
