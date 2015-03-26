# -*- coding: utf-8 -*-
"""
This gives other modules access to the gritty details about characters and the
encodings that use them.
"""

from __future__ import unicode_literals
import re
import zlib
import unicodedata
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

        # Build a regex from the ASCII range, followed by the decodings of
        # bytes 0x80-0xff in this character set. (This uses the fact that all
        # regex special characters are ASCII, and therefore won't appear in the
        # string.)
        regex = '^[\x00-\x7f{0}]*$'.format(charlist)
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
def _build_control_char_mapping():
    control_chars = {}
    for i in range(32):
        control_chars[i] = None

    # Map whitespace control characters to themselves.
    for char in '\t\n\f\r':
        del control_chars[ord(char)]
    return control_chars
CONTROL_CHARS = _build_control_char_mapping()


# A translate mapping that breaks ligatures made of Latin letters. While
# ligatures may be important to the representation of other languages, in
# Latin letters they tend to represent a copy/paste error.
#
# Ligatures may also be separated by NFKC normalization, but that is sometimes
# more normalization than you want.
LIGATURES = {
    ord('Ĳ'): 'IJ',
    ord('ĳ'): 'ij',
    ord('ﬀ'): 'ff',
    ord('ﬁ'): 'fi',
    ord('ﬂ'): 'fl',
    ord('ﬃ'): 'ffi',
    ord('ﬄ'): 'ffl',
    ord('ﬅ'): 'ſt',
    ord('ﬆ'): 'st'
}


# A translate mapping that replaces halfwidth and fullwidth forms with their
# standard-width forms.
def _build_width_map():
    width_map = {0x3000: ' '}
    for i in range(0xff01, 0xfff0):
        char = unichr(i)
        alternate = unicodedata.normalize('NFKC', char)
        if alternate != char:
            width_map[i] = alternate
    return width_map
WIDTH_MAP = _build_width_map()

