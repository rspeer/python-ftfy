# -*- coding: utf-8 -*-
"""
This gives other modules access to the gritty details about characters and the
encodings that use them.
"""

from __future__ import unicode_literals
import re
import zlib
from pkg_resources import resource_string
from ftfy.compatibility import unichr

# These are the five encodings we will try to fix in ftfy, in the
# order that they should be tried.
CHARMAP_ENCODINGS = [
    'latin-1',
    'sloppy-windows-1252',
    'macroman',
    'cp437',
    'sloppy-windows-1251',
]


def _build_regexes():
    """
    ENCODING_REGEXES contain reasonably fast ways to detect if we
    could represent a given string in a given encoding. The simplest one is
    the 'ascii' detector, which of course just determines if all characters
    are between U+0000 and U+007F.
    """
    # Define a regex that matches ASCII text.
    encoding_regexes = {'ascii': re.compile('^[\x00-\x7f]*$')}

    for encoding in CHARMAP_ENCODINGS:
        latin1table = ''.join(unichr(i) for i in range(128, 256))
        charlist = latin1table.encode('latin-1').decode(encoding)
        regex = '^[\x00-\x7f{}]*$'.format(charlist.replace('\\', '\\\\'))
        encoding_regexes[encoding] = re.compile(regex)
    return encoding_regexes
ENCODING_REGEXES = _build_regexes()


def possible_encoding(text, encoding):
    """
    Given text and a single-byte encoding, check whether that text could have
    been decoded from that single-byte encoding.

    In other words, check whether it can be encoded in that encoding, possibly
    sloppily.
    """
    return bool(ENCODING_REGEXES[encoding].match(text))


CHAR_CLASS_STRING = zlib.decompress(
    resource_string(__name__, 'char_classes.dat')
).decode('ascii')

def chars_to_classes(string):
    """
    Convert each Unicode character to a letter indicating which of many
    classes it's in.

    See build_data.py for where this data comes from and what it means.
    """
    return string.translate(CHAR_CLASS_STRING)


# A translate mapping that will strip all C0 control characters except
# those that represent whitespace.
CONTROL_CHARS = {}
for i in range(32):
    CONTROL_CHARS[i] = None

# Map whitespace control characters to themselves.
for char in '\t\n\f\r':
    del CONTROL_CHARS[ord(char)]
