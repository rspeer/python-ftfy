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


# These are encodings that map each byte to a particular character.
# They are listed in order of frequency, so that more frequent
# encodings will be tried first.
CHARMAP_ENCODINGS = [
    'windows-1252',
    'latin-1',
    'macroman',
    'cp437',
    'windows-1251',
]


def _build_charmaps():
    """
    CHARMAPS contains mappings from bytes to characters, for each single-byte
    encoding we know about.

    We don't use Python's decoders here because they're too strict. Many
    non-Python programs will leave mysterious bytes alone instead of raising
    an error or removing them. For example, Python will not decode 0x81 in
    Windows-1252 because it doesn't map to anything. Other systems will decode
    it to U+0081, which actually makes no sense because that's a meaningless
    control character from Latin-1, but I guess at least it preserves some
    information that ftfy can take advantage of.

    So that's what we do. When other systems decode 0x81 as U+0081, we match
    their behavior in case it helps us get reasonable text.

    Meanwhile, ENCODING_REGEXES contain reasonably fast ways to detect if we
    could represent a given string in a given encoding. The simplest one is
    the 'ascii' detector, which of course just determines if all characters
    are between U+0000 and U+007F.
    """
    charmaps = {}
    encoding_regexes = {'ascii': re.compile('^[\x00-\x7f]*$')}
    for encoding in CHARMAP_ENCODINGS:
        charmap = {}
        for codepoint in range(0, 0x80):
            charmap[codepoint] = unichr(codepoint)
        for codepoint in range(0x80, 0x100):
            char = unichr(codepoint)
            encoded_char = char.encode('latin-1')
            try:
                decoded_char = encoded_char.decode(encoding)
            except ValueError:
                decoded_char = char
            charmap[ord(decoded_char)] = char

        charlist = [unichr(codept) for codept in sorted(charmap.keys())
                    if codept >= 0x80]
        regex = '^[\x00-\x7f{}]*$'.format(''.join(charlist))
        charmaps[encoding] = charmap
        encoding_regexes[encoding] = re.compile(regex)
    return charmaps, encoding_regexes
CHARMAPS, ENCODING_REGEXES = _build_charmaps()


def possible_encoding(text, encoding):
    """
    Given text and a single-byte encoding, check whether that text could have
    been decoded from that single-byte encoding.
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

CONTROL_CHARS[ord('\t')] = '\t'
CONTROL_CHARS[ord('\n')] = '\n'
CONTROL_CHARS[ord('\f')] = '\f'
CONTROL_CHARS[ord('\r')] = '\r'
