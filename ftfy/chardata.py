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
            charmap[unichr(codepoint)] = unichr(codepoint)
        for codepoint in range(0x80, 0x100):
            char = unichr(codepoint)
            encoded_char = char.encode('latin-1')
            try:
                decoded_char = encoded_char.decode(encoding)
            except ValueError:
                decoded_char = char
            charmap[decoded_char] = char

        charlist = [char for char in sorted(charmap.keys()) if ord(char) >= 0x80]
        regex = '^[\x00-\x7f{}]*$'.format(''.join(charlist))
        CHARMAPS[encoding] = charmap
        encoding_regular_expressions[encoding] = re.compile(regex)

    encoding_regular_expressions['ascii'] = re.compile('^[\x00-\x7f]*')
    return encoding_regular_expressions

ENCODING_REGEXES = _make_encoding_regexes()


def possible_encoding(text, encoding):
    """
    Given text and a single-byte encoding, check whether that text could have
    been decoded from that single-byte encoding.
    """
    return bool(ENCODING_REGEXES[encoding].match(text))


# Make regular expressions out of categories of Unicode characters.
def _make_category_regex_ranges():
    encodable_char_set = set([unichr(codepoint) for codepoint in range(0, 0x100)])
    for codepoint in range(0x80, 0x100):
        encoded_char = chr(codepoint).encode('latin-1')
        for encoding in ['windows-1252', 'macroman', 'cp437']:
            try:
                decoded_char = encoded_char.decode(encoding)
                encodable_char_set.add(decoded_char)
            except ValueError:
                pass

    categories = defaultdict(list)
    for char in sorted(encodable_char_set):
        category = unicodedata.category(char)
        categories[category].append(char)

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
print(CATEGORY_RANGES)

# ----------------


# What is the heuristic for comparing single-byte encodings to each other?
encodable_chars = set()
for codepoint in range(0x80, 0x100):
    encoded_char = chr(codepoint).encode('latin-1')
    possibilities = []
    for encoding in ['latin-1', 'windows-1252', 'macroman', 'cp437']:
        try:
            decoded_char = encoded_char.decode(encoding)
            encodable_chars.add(decoded_char)
        except ValueError:
            decoded_char = encoded_char.decode('latin-1')
        possibilities.append(decoded_char)
    print(' '.join(possibilities))
print()

for char in sorted(encodable_chars):
    try:
        name = unicodedata.name(char)
    except ValueError:
        name = '[unknown]'
    print(char, hex(ord(char)), unicodedata.category(char), name)

# Rank the characters typically represented by a single byte -- that is, in
# Latin-1 or Windows-1252 -- by how weird it would be to see them in running
# text.
#
#   0 = not weird at all
#   1 = rare punctuation or rare letter that someone could certainly
#       have a good reason to use. All Windows-1252 gremlins are at least
#       weirdness 1.
#   2 = things that probably don't appear next to letters or other
#       symbols, such as math or currency symbols
#   3 = obscure symbols that nobody would go out of their way to use
#       (includes symbols that were replaced in ISO-8859-15)
#   4 = why would you use this?
#   5 = unprintable control character
#
# The Portuguese letter Ã (0xc3) is marked as weird because it would usually
# appear in the middle of a word in actual Portuguese, and meanwhile it
# appears in the mis-encodings of many common characters.


CHARACTER_WEIRDNESS = {
    # \xa0 to \xaf
    '\N{NO-BREAK SPACE}': 1,
    '\N{INVERTED EXCLAMATION MARK}': 1,
    '\N{CENT SIGN}': 2,
    '\N{POUND SIGN}': 2,
    '\N{CURRENCY SIGN}': 3,
    '\N{YEN SIGN}': 2,
    '\N{BROKEN BAR}': 4,
    '\N{SECTION SIGN}': 2,
    '\N{DIAERESIS}': 4,
    '\N{COPYRIGHT SIGN}': 2,
    '\N{FEMININE ORDINAL INDICATOR}': 3,
    # '\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}': 0,
    '\N{NOT SIGN}': 3,
    '\N{SOFT HYPHEN}': 1,
    '\N{REGISTERED SIGN}': 1,
    '\N{MACRON}': 4,

    # \xb0 to \xbf
    '\N{DEGREE SIGN}': 2,
    '\N{PLUS-MINUS SIGN}': 2,
    '\N{SUPERSCRIPT TWO}': 2,
    '\N{SUPERSCRIPT THREE}': 3,
    '\N{ACUTE ACCENT}': 3,
    '\N{MICRO SIGN}': 3,
    '\N{PILCROW SIGN}': 3,
    '\N{MIDDLE DOT}': 2,
    '\N{CEDILLA}': 4,
    '\N{SUPERSCRIPT ONE}': 4,
    '\N{MASCULINE ORDINAL INDICATOR}': 4,
    # '\N{RIGHT POINTING DOUBLE ANGLE QUOTATION MARK}': 0,
    '\N{VULGAR FRACTION ONE QUARTER}': 2,
    '\N{VULGAR FRACTION ONE HALF}': 2,
    '\N{VULGAR FRACTION THREE QUARTERS}': 2,
    '\N{INVERTED QUESTION MARK}': 0,

    # \xc0 to \xff
    '\N{LATIN CAPITAL LETTER A WITH TILDE}': 1,
    '\N{LATIN CAPITAL LETTER ETH}': 1,
    '\N{MULTIPLICATION SIGN}': 1,
    '\N{LATIN SMALL LETTER ETH}': 1,
    '\N{DIVISION SIGN}': 1,
    '\N{LATIN CAPITAL LETTER Y WITH DIAERESIS}': 1,

    # \U0100 to \U0200
    '\N{LATIN CAPITAL LETTER Y WITH DIAERESIS}': 1,
    '\N{LATIN SMALL LETTER F WITH HOOK}': 4,

    # \U0200 to \U0300
    '\N{MODIFIER LETTER CIRCUMFLEX ACCENT}': 1,
    '\N{CARON}': 3,
    '\N{BREVE}': 3,
    '\N{DOT ABOVE}': 3,
    '\N{RING ABOVE}': 3,
    '\N{OGONEK}': 3,
    '\N{SMALL TILDE}': 4,
    '\N{DOUBLE ACUTE ACCENT}': 3,

    # \U0300 to \U0400: selected Greek letters that were used in cp437.
    # You are probably not writing actual Greek with this small set of
    # letters.
    '\N{GREEK CAPITAL LETTER GAMMA}': 1,
    '\N{GREEK CAPITAL LETTER THETA}': 1,
    '\N{GREEK CAPITAL LETTER SIGMA}': 1,
    '\N{GREEK CAPITAL LETTER PHI}': 1,
    '\N{GREEK CAPITAL LETTER OMEGA}': 1,
    '\N{GREEK SMALL LETTER ALPHA}': 1,
    '\N{GREEK SMALL LETTER DELTA}': 1,
    '\N{GREEK SMALL LETTER EPSILON}': 1,
    '\N{GREEK SMALL LETTER PI}': 1,
    '\N{GREEK SMALL LETTER SIGMA}': 1,
    '\N{GREEK SMALL LETTER TAU}': 1,
    '\N{GREEK SMALL LETTER PHI}': 1,

    # \U2000 to \U2400
    '\N{DAGGER}': 2,
    '\N{DOUBLE DAGGER}': 3,
    '\N{PER MILLE SIGN}': 4,
    '\N{FRACTION SLASH}': 2,
    '\N{SUPERSCRIPT LATIN SMALL LETTER N}': 3,
    '\N{PESETA SIGN}': 3,
    '\N{NUMERO SIGN}': 2,
    '\N{PARTIAL DIFFERENTIAL}': 1,
    '\N{INCREMENT}': 1,
    '\N{N-ARY PRODUCT}': 2,
    '\N{N-ARY SUMMATION}': 2,
    '\N{SQUARE ROOT}': 1,
    '\N{INFINITY}': 1,
    '\N{INTERSECTION}': 2,
    '\N{INTEGRAL}': 2,
    '\N{ALMOST EQUAL TO}': 1,
    '\N{NOT EQUAL TO}': 1,
    '\N{IDENTICAL TO}': 2,
    '\N{LESS-THAN OR EQUAL TO}': 1,
    '\N{GREATER-THAN OR EQUAL TO}': 1,
    '\N{REVERSED NOT SIGN}': 4,
    '\N{TOP HALF INTEGRAL}': 3,
    '\N{BOTTOM HALF INTEGRAL}': 3,

    # \U2500 to \U2600 are mostly box drawings; they're okay, or at least
    # require a different heuristic
    '\N{LOZENGE}': 2,
    '\uf8ff': 2,   # the Apple symbol
    '\N{LATIN SMALL LIGATURE FI}': 1,
    '\N{LATIN SMALL LIGATURE FL}': 1,
}



# Create a fast mapping that converts a Unicode string to a string describing
# its character classes, particularly the scripts its letters are in.
#
# Capital letters represent groups of commonly-used scripts:
#   L = Latin
#   E = several East Asian scripts including hanzi, kana, and Hangul
#   C = Cyrillic
#   etc.
#
# Lowercase letters represent rare scripts.
# . represents non-letters.
# Whitespace represents whitespace.
# ? represents errors.
#
# Astral characters pass through unmodified; we don't count them as script
# conflicts. They are probably intentional.

SCRIPT_LETTERS = {
    'LATIN': 'L',
    'CJK': 'E',
    'ARABIC': 'A',
    'CYRILLIC': 'C',
    'GREEK': 'G',
    'HEBREW': 'H',
    'KATAKANA': 'E',
    'HIRAGANA': 'E',
    'HIRAGANA-KATAKANA': 'E',
    'KATAKANA-HIRAGANA': 'E',
    'HANGUL': 'E',
    'DEVANAGARI': 'D',
    'THAI': 'T',
    'FULLWIDTH': 'E',
    'MASCULINE': 'L',
    'FEMININE': 'L',
    'MODIFIER': '.',
    'HALFWIDTH': 'E',
    'BENGALI': 'b',
    'LAO': 'l',
    'KHMER': 'k',
    'TELUGU': 't',
    'MALAYALAM': 'm',
    'SINHALA': 's',
    'TAMIL': 'a',
    'GEORGIAN': 'g',
    'ARMENIAN': 'r',
    'KANNADA': 'n',  # mostly used for looks of disapproval
}


SCRIPT_MAP = {}

for codepoint in range(0x10000):
    char = unichr(codepoint)
    if unicodedata.category(char).startswith('L'):
        try:
            name = unicodedata.name(char)
            script = name.split()[0]
            if script in SCRIPT_LETTERS:
                SCRIPT_MAP[codepoint] = SCRIPT_LETTERS[script]
            else:
                SCRIPT_MAP[codepoint] = 'z'
        except ValueError:
            # it's unfortunate that this gives subtly different results
            # on Python 2.6, which is confused about the Unicode 5.1
            # Chinese range. It knows they're letters but it has no idea
            # what they are named.
            #
            # This could be something to fix in the future, or maybe we
            # just stop supporting Python 2.6 eventually.
            SCRIPT_MAP[codepoint] = 'z'
    elif unicodedata.category(char).startswith('Z'):
        SCRIPT_MAP[codepoint] = ' '
    elif unicodedata.category(char) == 'Cn':
        SCRIPT_MAP[codepoint] = '?'
    else:
        SCRIPT_MAP[codepoint] = '.'

SCRIPT_MAP[0x09] = ' '
SCRIPT_MAP[0x0a] = '\n'
SCRIPT_MAP[0xfffd] = '?'


# A translate mapping that will strip all control characters except \t and \n.
# This incidentally has the effect of normalizing Windows \r\n line endings to
# Unix \n line endings.
CONTROL_CHARS = {}
for i in range(256):
    if unicodedata.category(unichr(i)) == 'Cc':
        CONTROL_CHARS[i] = None

CONTROL_CHARS[ord('\t')] = '\t'
CONTROL_CHARS[ord('\n')] = '\n'
