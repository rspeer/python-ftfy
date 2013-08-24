# -*- coding: utf-8 -*-
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
CONFUSABLE_1BYTE_ENCODINGS = [
    'windows-1252',
    'macroman',
    'cp437'
]
CHARMAPS = {}

def _make_encoding_regexes():
    encoding_regular_expressions = {}

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

        charlist = [unichr(codept) for codept in sorted(charmap.keys()) if codept >= 0x80]
        regex = '^[\x00-\x7f{}]*$'.format(''.join(charlist))
        CHARMAPS[encoding] = charmap
        encoding_regular_expressions[encoding] = re.compile(regex)

    encoding_regular_expressions['ascii'] = re.compile('^[\x00-\x7f]*$')
    return encoding_regular_expressions

ENCODING_REGEXES = _make_encoding_regexes()


def possible_encoding(text, encoding):
    """
    Given text and a single-byte encoding, check whether that text could have
    been decoded from that single-byte encoding.
    """
    return bool(ENCODING_REGEXES[encoding].match(text))


CHAR_CLASS_STRING = zlib.decompress(resource_string(__name__, 'char_classes.dat')).decode('ascii')

def chars_to_classes(string):
    return string.translate(CHAR_CLASS_STRING)

# A translate mapping that will strip all C0 control characters except
# \t and \n. This incidentally has the effect of normalizing Windows \r\n
# line endings to Unix \n line endings.
CONTROL_CHARS = {}
for i in range(32):
    CONTROL_CHARS[i] = None

CONTROL_CHARS[ord('\t')] = '\t'
CONTROL_CHARS[ord('\n')] = '\n'
CONTROL_CHARS[ord('\f')] = '\f'
CONTROL_CHARS[ord('\r')] = '\r'
