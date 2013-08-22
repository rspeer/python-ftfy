# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unicodedata
import sys
import re
import zlib
from pkg_resources import resource_string

if sys.hexversion >= 0x03000000:
    unichr = chr
    xrange = range

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


# L = Latin capital letter
# l = Latin lowercase letter
# A = Non-latin capital or title-case letter
# a = Non-latin lowercase letter
# C = Non-cased letter (Lo)
# X = Control character (Cc)
# m = Letter modifier (Lm)
# M = Mark (Mc, Me, Mn)
# N = Miscellaneous numbers (No)
# 0 = Math symbol (Sm)
# 1 = Currency symbol (Sc)
# 2 = Symbol modifier (Sk)
# 3 = Other symbol (So)
# S = UTF-16 surrogate
# _ = Unassigned character
#   = Whitespace
# o = Other

def _make_char_class_letters():
    cclasses = [None] * 0x110000
    for codepoint in range(0x0, 0x110000):
        char = unichr(codepoint)
        category = unicodedata.category(char)

        if category.startswith('L'):  # letters
            if unicodedata.name(char).startswith('LATIN')\
            and codepoint < 0x200:
                if category == 'Lu':
                    cclasses[codepoint] = 'L'
                else:
                    cclasses[codepoint] = 'l'
            else: # non-Latin letter, or close enough
                if category == 'Lu' or category == 'Lt':
                    cclasses[codepoint] = 'A'
                elif category == 'Ll':
                    cclasses[codepoint] = 'a'
                elif category == 'Lo':
                    cclasses[codepoint] = 'C'
                elif category == 'Lm':
                    cclasses[codepoint] = 'm'
                else:
                    raise ValueError('got some weird kind of letter')
        elif category.startswith('M'):  # marks
            cclasses[codepoint] = 'M'
        elif category == 'No':
            cclasses[codepoint] = 'N'
        elif category == 'Sm':
            cclasses[codepoint] = '0'
        elif category == 'Sc':
            cclasses[codepoint] = '1'
        elif category == 'Sk':
            cclasses[codepoint] = '2'
        elif category == 'So':
            cclasses[codepoint] = '3'
        elif category == 'Cn':
            cclasses[codepoint] = '_'
        elif category == 'Cc':
            cclasses[codepoint] = 'X'
        elif category == 'Cs':
            cclasses[codepoint] = 'S'
        elif category.startswith('Z'):
            cclasses[codepoint] = ' '
        else:
            cclasses[codepoint] = 'o'
    
    cclasses[9] = cclasses[10] = cclasses[12] = cclasses[13] = ' '
    out = open('char_classes.dat', 'wb')
    out.write(zlib.compress(bytes(''.join(cclasses), 'ascii')))
    out.close()

CHAR_CLASS_STRING = zlib.decompress(resource_string(__name__, 'char_classes.dat')).decode('ascii')

def chars_to_classes(string):
    return string.translate(CHAR_CLASS_STRING)

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
