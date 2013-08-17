# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unicodedata
import sys
import re
from collections import defaultdict

if sys.hexversion >= 0x03000000:
    unichr = chr

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


# Make regular expressions out of categories of Unicode characters.
# Except we probably need broader ranges.
#
# Ll Lu: weirdness=1
# Ll [Lo Lt]: weirdness=2
# Lm Sk Sm Sc No So Po
def _make_category_regex_ranges():
    categories = defaultdict(list)
    for codepoint in range(0x20, 0x10000):
        char = unichr(codepoint)
        category = unicodedata.category(char)
        categories[category].append(char)
        
        # Find Latin vs. non-Latin letters
        if category.startswith('L'):
            if unicodedata.name(char).startswith('LATIN')\
            and codepoint < 0x200:
                categories['latin'].append(char)
            else:
                categories['nonlatin'].append(char)

    ranges = {}
    for category in categories:
        ranges[category] = (''.join(categories[category])
                              .replace('\\', '\\\\')
                              .replace('[', r'\[')
                              .replace(']', r'\]')
                              .replace('^', r'\^')
                              .replace('-', r'\-'))

    return ranges
CATEGORY_RANGES = _make_category_regex_ranges()

# Separate out non-ASCII uppercase characters
_non_ascii_upper = ''.join(
    ch for ch in CATEGORY_RANGES['Lu']
    if ord(ch) >= 0x80
)
_non_ascii_lower = ''.join(
    ch for ch in CATEGORY_RANGES['Ll']
    if ord(ch) >= 0x80
)
CATEGORY_RANGES['Lun'] = _non_ascii_upper
CATEGORY_RANGES['Lln'] = _non_ascii_lower


# A translate mapping that will strip all control characters except \t and \n.
# This incidentally has the effect of normalizing Windows \r\n line endings to
# Unix \n line endings.
CONTROL_CHARS = {}
for i in range(256):
    if unicodedata.category(unichr(i)) == 'Cc':
        CONTROL_CHARS[i] = None

CONTROL_CHARS[ord('\t')] = '\t'
CONTROL_CHARS[ord('\n')] = '\n'
CONTROL_CHARS[ord('\f')] = '\f'
CONTROL_CHARS[ord('\r')] = '\r'
