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
    CHARMAPS is a list of 'translate' mappings. For every character map that
    we care about, it will contain a mapping *from* the Unicode characters in
    that character set, *to* characters that stand in for bytes.

    It would be a lot cleaner if we could map the characters directly to
    bytes, but the output of ``str.translate`` (``unicode.translate`` in
    Python 2) has to be a Unicode string, not bytes.

    So when you use these mappings with Unicode, what you're doing is mapping
    a certain character set onto the first 256 Unicode characters, like a
    chump who doesn't know anything about Unicode. But then you can take the
    resulting string, and encode it as `latin-1`, and you get back the
    appropriate bytes. Two wrongs *do* make a right sometimes!

    We don't use Python's encoders here because they're too strict. For
    example, the Windows-1252 character map has some holes in it, including
    0x81. There is no assigned meaning to byte 0x81, so if you try to decode
    it, Python will raise an error.

    But some other environments, such as web browsers, don't have the luxury
    of raising errors when they see something unexpected. What they will
    typically do is map 0x81 to Unicode character U+0081, a character which
    is basically reserved for that purpose anyway. We'll call this "sloppy
    decoding".

    So now you've got some text that came from the Web, and it contains
    U+0081 because it was sloppily decoded as Windows-1252. How do we get
    back what the bytes were? Well, we need to sloppily *encode*. We need
    a version of Windows-1252 where U+0081 gets encoded as 0x81, instead
    of just raising an error.

    So that's what we do. When other systems decode 0x81 as U+0081, we support
    that by encoding U+0081 as 0x81, in case it helps us get reasonable text.

    Meanwhile, ENCODING_REGEXES contain reasonably fast ways to detect if we
    could represent a given string in a given encoding. The simplest one is
    the 'ascii' detector, which of course just determines if all characters
    are between U+0000 and U+007F.
    """
    charmaps = {}

    # Define a regex that matches ASCII text.
    encoding_regexes = {'ascii': re.compile('^[\x00-\x7f]*$')}

    # For each character map encoding we care about, make a regex that contains
    # all the characters that that encoding supports, and a mapping from those
    # characters to sorta-bytes.
    for encoding in CHARMAP_ENCODINGS:
        charmap = {}
        for codepoint in range(0, 0x80):
            # ASCII characters map to themselves.
            charmap[codepoint] = unichr(codepoint)
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

        # Put together all the characters we got, and make a regular expression
        # that matches all of them.
        charlist = [unichr(codept) for codept in sorted(charmap.keys())
                    if codept >= 0x80]
        regex = '^[\x00-\x7f{0}]*$'.format(''.join(charlist))

        # Store the mapping and the regex in the dictionaries we're returning.
        charmaps[encoding] = charmap
        encoding_regexes[encoding] = re.compile(regex)
    return charmaps, encoding_regexes
CHARMAPS, ENCODING_REGEXES = _build_charmaps()


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
