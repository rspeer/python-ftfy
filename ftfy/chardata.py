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
import ftfy.bad_codecs

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
    [outdated docs]

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
    inverse_charmaps = {}
    encoding_regexes = {
        'ascii': re.compile('^[\x00-\x7f]*$'),
    }
    for encoding in CHARMAP_ENCODINGS:
        charmap = {}
        inverse_charmap = {}
        for codepoint in range(0, 0x80):
            # ASCII characters map to themselves.
            charmap[codepoint] = unichr(codepoint)
            inverse_charmap[codepoint] = unichr(codepoint)
        for codepoint in range(0x80, 0x100):
            # The other characters map to characters from U+0080 to U+00FF,
            # standing in for bytes. We call these sorta-bytes.
            char = unichr(codepoint)

            # Turn the sorta-byte into a byte, and try decoding it.
            encoded_char = char.encode('latin-1')
            try:
                # It decoded, so that's the character we need to add to our
                # character map.
                decoded_char = encoded_char.decode(encoding)
            except ValueError:
                # It didn't decode, so we should be "sloppy" and add the
                # sorta-byte itself to the character map.
                decoded_char = char
            charmap[ord(decoded_char)] = char
            inverse_charmap[ord(char)] = decoded_char

        # Put together all the characters we got, and make a regular expression
        # that matches all of them.
        charlist = [unichr(codept) for codept in sorted(charmap.keys())
                    if codept >= 0x80]
        regex = '^[\x00-\x7f{0}]*$'.format(''.join(charlist))

        # Store the mapping and the regex in the dictionaries we're returning.
        charmaps[encoding] = charmap
        inverse_charmaps[encoding] = inverse_charmap
        latin1table = ''.join(unichr(i) for i in range(256))
        charlist = latin1table.encode('latin-1').decode(encoding)
        regex = '^[\x00-\x7f{}]*$'.format(charlist)
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
