"""
This gives other modules access to the gritty details about characters and the
encodings that use them.
"""

import html
import itertools
import re
import unicodedata
import zlib


# These are the encodings we will try to fix in ftfy, in the
# order that they should be tried.
CHARMAP_ENCODINGS = [
    'latin-1',
    'sloppy-windows-1252',
    'sloppy-windows-1251',
    'sloppy-windows-1250',
    'sloppy-windows-1253',
    'sloppy-windows-1254',
    'iso-8859-2',
    'macroman',
    'cp437',
]

SINGLE_QUOTE_RE = re.compile('[\u02bc\u2018-\u201b]')
DOUBLE_QUOTE_RE = re.compile('[\u201c-\u201f]')


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
        # Make a sequence of characters that bytes \x80 to \xFF decode to
        # in each encoding, as well as byte \x1A, which is used to represent
        # the replacement character � in the sloppy-* encodings.
        byte_range = bytes(list(range(0x80, 0x100)) + [0x1a])
        charlist = byte_range.decode(encoding)

        # The rest of the ASCII bytes -- bytes \x00 to \x19 and \x1B
        # to \x7F -- will decode as those ASCII characters in any encoding we
        # support, so we can just include them as ranges. This also lets us
        # not worry about escaping regex special characters, because all of
        # them are in the \x1B to \x7F range.
        regex = '^[\x00-\x19\x1b-\x7f{0}]*$'.format(charlist)
        encoding_regexes[encoding] = re.compile(regex)
    return encoding_regexes


ENCODING_REGEXES = _build_regexes()


def _build_html_entities():
    entities = {}
    # Create a dictionary based on the built-in HTML5 entity dictionary.
    # Add a limited set of HTML entities that we'll also decode if they've
    # been case-folded to uppercase, such as decoding &NTILDE; as "Ñ".
    for name, char in html.entities.html5.items():
        if name.endswith(';'):
            entities['&' + name] = char

            # Restrict the set of characters we can attempt to decode if their
            # name has been uppercased. If we tried to handle all entity names,
            # the results would be ambiguous.
            if name == name.lower():
                name_upper = name.upper()
                entity_upper = '&' + name_upper
                if html.unescape(entity_upper) == entity_upper:
                    entities[entity_upper] = char.upper()
    return entities


HTML_ENTITY_RE = re.compile(r"&#?[0-9A-Za-z]{1,24};")
HTML_ENTITIES = _build_html_entities()


def possible_encoding(text, encoding):
    """
    Given text and a single-byte encoding, check whether that text could have
    been decoded from that single-byte encoding.

    In other words, check whether it can be encoded in that encoding, possibly
    sloppily.
    """
    return bool(ENCODING_REGEXES[encoding].match(text))


def _build_control_char_mapping():
    """
    Build a translate mapping that strips likely-unintended control characters.
    See :func:`ftfy.fixes.remove_control_chars` for a description of these
    codepoint ranges and why they should be removed.
    """
    control_chars = {}

    for i in itertools.chain(
        range(0x00, 0x09),
        [0x0b],
        range(0x0e, 0x20),
        [0x7f],
        range(0x206a, 0x2070),
        [0xfeff],
        range(0xfff9, 0xfffd),
    ):
        control_chars[i] = None

    return control_chars


CONTROL_CHARS = _build_control_char_mapping()


# Recognize UTF-8 sequences that would be valid if it weren't for a b'\xa0'
# that some Windows-1252 program converted to a plain space.
#
# The smaller values are included on a case-by-case basis, because we don't want
# to decode likely input sequences to unlikely characters. These are the ones
# that *do* form likely characters before 0xa0:
#
#   0xc2 -> U+A0 NO-BREAK SPACE
#   0xc3 -> U+E0 LATIN SMALL LETTER A WITH GRAVE
#   0xc5 -> U+160 LATIN CAPITAL LETTER S WITH CARON
#   0xce -> U+3A0 GREEK CAPITAL LETTER PI
#   0xd0 -> U+420 CYRILLIC CAPITAL LETTER ER
#
# In four-character sequences, the lead byte must be F0, because that accounts
# for almost all of the usage of high-numbered codepoints (tag characters whose
# UTF-8 starts with the byte F3 are only used in some rare new emoji sequences).
#
# This is meant to be applied to encodings of text that tests true for `is_bad`.
# Any of these could represent characters that legitimately appear surrounded by
# spaces, particularly U+C5 (Å), which is a word in multiple languages!
#
# We should consider checking for b'\x85' being converted to ... in the future.
# I've seen it once, but the text still wasn't recoverable.

ALTERED_UTF8_RE = re.compile(
    b'[\xc2\xc3\xc5\xce\xd0][ ]'
    b'|[\xe0-\xef][ ][\x80-\xbf]'
    b'|[\xe0-\xef][\x80-\xbf][ ]'
    b'|[\xf0][ ][\x80-\xbf][\x80-\xbf]'
    b'|[\xf0][\x80-\xbf][ ][\x80-\xbf]'
    b'|[\xf0][\x80-\xbf][\x80-\xbf][ ]'
)


# This expression matches UTF-8 and CESU-8 sequences where some of the
# continuation bytes have been lost. The byte 0x1a (sometimes written as ^Z) is
# used within ftfy to represent a byte that produced the replacement character
# \ufffd. We don't know which byte it was, but we can at least decode the UTF-8
# sequence as \ufffd instead of failing to re-decode it at all.
#
# In some cases, we allow the ASCII '?' in place of \ufffd, but at most once per
# sequence.
LOSSY_UTF8_RE = re.compile(                                                                                            
    b'[\xc2-\xdf][\x1a]'
    b'|[\xc2-\xc3][?]'
    b'|\xed[\xa0-\xaf][\x1a?]\xed[\xb0-\xbf][\x1a?\x80-\xbf]'
    b'|\xed[\xa0-\xaf][\x1a?\x80-\xbf]\xed[\xb0-\xbf][\x1a?]'
    b'|[\xe0-\xef][\x1a?][\x1a\x80-\xbf]'
    b'|[\xe0-\xef][\x1a\x80-\xbf][\x1a?]'
    b'|[\xf0-\xf4][\x1a?][\x1a\x80-\xbf][\x1a\x80-\xbf]'
    b'|[\xf0-\xf4][\x1a\x80-\xbf][\x1a?][\x1a\x80-\xbf]'
    b'|[\xf0-\xf4][\x1a\x80-\xbf][\x1a\x80-\xbf][\x1a?]'
    b'|\x1a'
)


# This regex matches C1 control characters, which occupy some of the positions
# in the Latin-1 character map that Windows assigns to other characters instead.
C1_CONTROL_RE = re.compile(r'[\x80-\x9f]')


# A translate mapping that breaks ligatures made of Latin letters. While
# ligatures may be important to the representation of other languages, in Latin
# letters they tend to represent a copy/paste error. It omits ligatures such
# as æ that are frequently used intentionally.
#
# This list additionally includes some Latin digraphs that represent two
# characters for legacy encoding reasons, not for typographical reasons.
#
# Ligatures and digraphs may also be separated by NFKC normalization, but that
# is sometimes more normalization than you want.

LIGATURES = {
    ord('Ĳ'): 'IJ',  # Dutch ligatures
    ord('ĳ'): 'ij',
    ord('ŉ'): "ʼn",  # Afrikaans digraph meant to avoid auto-curled quote
    ord('Ǳ'): 'DZ',  # Serbian/Croatian digraphs for Cyrillic conversion
    ord('ǲ'): 'Dz',
    ord('ǳ'): 'dz',
    ord('Ǆ'): 'DŽ',
    ord('ǅ'): 'Dž',
    ord('ǆ'): 'dž',
    ord('Ǉ'): 'LJ',
    ord('ǈ'): 'Lj',
    ord('ǉ'): 'lj',
    ord('Ǌ'): 'NJ',
    ord('ǋ'): 'Nj',
    ord('ǌ'): "nj",
    ord('ﬀ'): 'ff',  # Latin typographical ligatures
    ord('ﬁ'): 'fi',
    ord('ﬂ'): 'fl',
    ord('ﬃ'): 'ffi',
    ord('ﬄ'): 'ffl',
    ord('ﬅ'): 'ſt',
    ord('ﬆ'): 'st',
}


def _build_width_map():
    """
    Build a translate mapping that replaces halfwidth and fullwidth forms
    with their standard-width forms.
    """
    # Though it's not listed as a fullwidth character, we'll want to convert
    # U+3000 IDEOGRAPHIC SPACE to U+20 SPACE on the same principle, so start
    # with that in the dictionary.
    width_map = {0x3000: ' '}
    for i in range(0xff01, 0xfff0):
        char = chr(i)
        alternate = unicodedata.normalize('NFKC', char)
        if alternate != char:
            width_map[i] = alternate
    return width_map


WIDTH_MAP = _build_width_map()


def _char_range(start, end):
    """
    Get a contiguous range of characters as a string. Useful for including
    in a regex without making the representation _only_ usable in regexes.
    """
    return ''.join(chr(codept) for codept in range(start, end + 1))


# There are only 403 characters that occur in known UTF-8 mojibake, and we can
# characterize them:

MOJIBAKE_CATEGORIES = {
    # Characters that appear in many different contexts. Sequences that contain
    # them are not inherently mojibake
    'common': (
        '\N{NO-BREAK SPACE}'
        '\N{SOFT HYPHEN}'
        '\N{MIDDLE DOT}'
        '\N{ACUTE ACCENT}'
        '\N{EN DASH}'
        '\N{EM DASH}'
        '\N{HORIZONTAL BAR}'
        '\N{HORIZONTAL ELLIPSIS}'
        '\N{RIGHT SINGLE QUOTATION MARK}'
    ),
    # the C1 control character range, which have no uses outside of mojibake anymore
    'c1': _char_range(0x80, 0x9f),
    # Characters that are nearly 100% used in mojibake
    'bad': (
        '\N{BROKEN BAR}'
        '\N{CURRENCY SIGN}'
        '\N{DIAERESIS}'
        '\N{NOT SIGN}'
        '\N{MACRON}'
        '\N{PILCROW SIGN}'
        '\N{CEDILLA}'
        '\N{LATIN SMALL LETTER F WITH HOOK}'
        '\N{MODIFIER LETTER CIRCUMFLEX ACCENT}'  # it's not a modifier
        '\N{CARON}'
        '\N{BREVE}'
        '\N{OGONEK}'
        '\N{SMALL TILDE}'
        '\N{DAGGER}'
        '\N{DOUBLE DAGGER}'
        '\N{PER MILLE SIGN}'
        '\N{REVERSED NOT SIGN}'
        '\N{LOZENGE}'
        '\ufffd'

        # Theoretically these would appear in 'numeric' contexts, but when they
        # co-occur with other mojibake characters, it's not really ambiguous
        '\N{FEMININE ORDINAL INDICATOR}'
        '\N{MASCULINE ORDINAL INDICATOR}'
        '\N{NUMERO SIGN}'
    ),
    'currency': (
        '\N{CENT SIGN}'
        '\N{POUND SIGN}'
        '\N{YEN SIGN}'
        '\N{PESETA SIGN}'
        '\N{EURO SIGN}'
    ),
    'start_punctuation': (
        '\N{INVERTED EXCLAMATION MARK}'
        '\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}'
        '\N{INVERTED QUESTION MARK}'
        '\N{COPYRIGHT SIGN}'
        '\N{SECTION SIGN}'
        '\N{GREEK TONOS}'
        '\N{GREEK DIALYTIKA TONOS}'
        '\N{LEFT SINGLE QUOTATION MARK}'
        '\N{SINGLE LOW-9 QUOTATION MARK}'
        '\N{LEFT DOUBLE QUOTATION MARK}'
        '\N{DOUBLE LOW-9 QUOTATION MARK}'
        '\N{BULLET}'
        '\N{SINGLE LEFT-POINTING ANGLE QUOTATION MARK}'
        '\uf8ff'  # OS-specific symbol, usually the Apple logo
    ),
    'end_punctuation': (
        '\N{REGISTERED SIGN}'
        '\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}'
        '\N{DOUBLE ACUTE ACCENT}'
        '\N{RIGHT DOUBLE QUOTATION MARK}'
        '\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}'
        '\N{TRADE MARK SIGN}'
    ),
    'numeric': (
        '\N{SUPERSCRIPT TWO}'
        '\N{SUPERSCRIPT THREE}'
        '\N{SUPERSCRIPT ONE}'
        '\N{PLUS-MINUS SIGN}'
        '\N{VULGAR FRACTION ONE QUARTER}'
        '\N{VULGAR FRACTION ONE HALF}'
        '\N{VULGAR FRACTION THREE QUARTERS}'
        '\N{MULTIPLICATION SIGN}'
        '\N{MICRO SIGN}'
        '\N{DIVISION SIGN}'
        '\N{FRACTION SLASH}'
        '\N{PARTIAL DIFFERENTIAL}'
        '\N{INCREMENT}'
        '\N{N-ARY PRODUCT}'
        '\N{N-ARY SUMMATION}'
        '\N{SQUARE ROOT}'
        '\N{INFINITY}'
        '\N{INTERSECTION}'
        '\N{INTEGRAL}'
        '\N{ALMOST EQUAL TO}'
        '\N{NOT EQUAL TO}'
        '\N{IDENTICAL TO}'
        '\N{LESS-THAN OR EQUAL TO}'
        '\N{GREATER-THAN OR EQUAL TO}'
    ),
    'kaomoji': (
        _char_range(0xd2, 0xd6)
        + _char_range(0xd9, 0xdc)
        + _char_range(0xf2, 0xf6)
        + _char_range(0xf8, 0xfc) +
        '\N{LATIN CAPITAL LETTER O WITH DOUBLE ACUTE}'
        '\N{DEGREE SIGN}'
    ),
    'upper_accented': (
        _char_range(0xc0, 0xd1) +
        # skip capital O's and U's that could be used in kaomoji, but
        # include Ø because it's very common in Arabic mojibake:
        '\N{LATIN CAPITAL LETTER O WITH STROKE}'
        '\N{LATIN CAPITAL LETTER U WITH DIAERESIS}'
        '\N{LATIN CAPITAL LETTER Y WITH ACUTE}'
        '\N{LATIN CAPITAL LETTER A WITH BREVE}'
        '\N{LATIN CAPITAL LETTER A WITH OGONEK}'
        '\N{LATIN CAPITAL LETTER C WITH ACUTE}'
        '\N{LATIN CAPITAL LETTER C WITH CARON}'
        '\N{LATIN CAPITAL LETTER D WITH CARON}'
        '\N{LATIN CAPITAL LETTER D WITH STROKE}'
        '\N{LATIN CAPITAL LETTER E WITH OGONEK}'
        '\N{LATIN CAPITAL LETTER E WITH CARON}'
        '\N{LATIN CAPITAL LETTER G WITH BREVE}'
        '\N{LATIN CAPITAL LETTER I WITH DOT ABOVE}'
        '\N{LATIN CAPITAL LETTER L WITH ACUTE}'
        '\N{LATIN CAPITAL LETTER L WITH CARON}'
        '\N{LATIN CAPITAL LETTER L WITH STROKE}'
        '\N{LATIN CAPITAL LETTER N WITH ACUTE}'
        '\N{LATIN CAPITAL LETTER N WITH CARON}'
        '\N{LATIN CAPITAL LIGATURE OE}'
        '\N{LATIN CAPITAL LETTER R WITH CARON}'
        '\N{LATIN CAPITAL LETTER S WITH ACUTE}'
        '\N{LATIN CAPITAL LETTER S WITH CEDILLA}'
        '\N{LATIN CAPITAL LETTER S WITH CARON}'
        '\N{LATIN CAPITAL LETTER T WITH CEDILLA}'
        '\N{LATIN CAPITAL LETTER T WITH CARON}'
        '\N{LATIN CAPITAL LETTER U WITH RING ABOVE}'
        '\N{LATIN CAPITAL LETTER U WITH DOUBLE ACUTE}'
        '\N{LATIN CAPITAL LETTER Y WITH DIAERESIS}'
        '\N{LATIN CAPITAL LETTER Z WITH ACUTE}'
        '\N{LATIN CAPITAL LETTER Z WITH DOT ABOVE}'
        '\N{LATIN CAPITAL LETTER Z WITH CARON}'
        '\N{CYRILLIC CAPITAL LETTER GHE WITH UPTURN}'
    ),
    'lower_accented': (
        '\N{LATIN SMALL LETTER SHARP S}'
        + _char_range(0xe0, 0xf1) +
        # skip o's and u's that could be used in kaomoji
        '\N{LATIN SMALL LETTER A WITH BREVE}'
        '\N{LATIN SMALL LETTER A WITH OGONEK}'
        '\N{LATIN SMALL LETTER C WITH ACUTE}'
        '\N{LATIN SMALL LETTER C WITH CARON}'
        '\N{LATIN SMALL LETTER D WITH CARON}'
        '\N{LATIN SMALL LETTER D WITH STROKE}'
        '\N{LATIN SMALL LETTER E WITH OGONEK}'
        '\N{LATIN SMALL LETTER E WITH CARON}'
        '\N{LATIN SMALL LETTER G WITH BREVE}'
        '\N{LATIN SMALL LETTER L WITH ACUTE}'
        '\N{LATIN SMALL LETTER L WITH CARON}'
        '\N{LATIN SMALL LETTER L WITH STROKE}'
        '\N{LATIN SMALL LIGATURE OE}'
        '\N{LATIN SMALL LETTER R WITH ACUTE}'
        '\N{LATIN SMALL LETTER S WITH ACUTE}'
        '\N{LATIN SMALL LETTER S WITH CEDILLA}'
        '\N{LATIN SMALL LETTER S WITH CARON}'
        '\N{LATIN SMALL LETTER T WITH CARON}'
        '\N{LATIN SMALL LETTER Z WITH ACUTE}'
        '\N{LATIN SMALL LETTER Z WITH DOT ABOVE}'
        '\N{LATIN SMALL LETTER Z WITH CARON}'
        '\N{CYRILLIC SMALL LETTER GHE WITH UPTURN}'
        '\N{LATIN SMALL LIGATURE FI}'
        '\N{LATIN SMALL LIGATURE FL}'
    ),
    'upper_common': (
        '\N{LATIN CAPITAL LETTER THORN}'
        + _char_range(0x391, 0x3a9) +  # Greek capital letters

        # not included under 'accented' because these can commonly
        # occur at ends of words, in positions where they'd be detected
        # as mojibake
        '\N{GREEK CAPITAL LETTER ALPHA WITH TONOS}'
        '\N{GREEK CAPITAL LETTER EPSILON WITH TONOS}'
        '\N{GREEK CAPITAL LETTER ETA WITH TONOS}'
        '\N{GREEK CAPITAL LETTER IOTA WITH TONOS}'
        '\N{GREEK CAPITAL LETTER OMICRON WITH TONOS}'
        '\N{GREEK CAPITAL LETTER UPSILON WITH TONOS}'
        '\N{GREEK CAPITAL LETTER OMEGA WITH TONOS}'
        '\N{GREEK CAPITAL LETTER IOTA WITH DIALYTIKA}'
        '\N{GREEK CAPITAL LETTER UPSILON WITH DIALYTIKA}'
        + _char_range(0x401, 0x42f)  # Cyrillic capital letters
    ),
    'lower_common': (
        # lowercase thorn does not appear in mojibake
        _char_range(0x3b1, 0x3c6) +  # Greek lowercase letters
        '\N{GREEK SMALL LETTER ALPHA WITH TONOS}'
        '\N{GREEK SMALL LETTER EPSILON WITH TONOS}'
        '\N{GREEK SMALL LETTER ETA WITH TONOS}'
        '\N{GREEK SMALL LETTER IOTA WITH TONOS}'
        '\N{GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND TONOS}'
        + _char_range(0x430, 0x45f)  # Cyrillic lowercase letters
    ),
    'box': (
        '─│┌┐┘├┤┬┼'
        + _char_range(0x2550, 0x256c) +
        '▀▄█▌▐░▒▓'
    ),
}


BADNESS_RE = re.compile("""
    [{c1}]
    |
    [{bad}{lower_accented}{upper_accented}{box}{start_punctuation}{end_punctuation}{currency}{numeric}] [{bad}]
    |
    [{bad}] [{lower_accented}{upper_accented}{box}{start_punctuation}{end_punctuation}{currency}{numeric}]
    |
    [{lower_accented}{lower_common}{box}{end_punctuation}{currency}{numeric}] [{upper_accented}]
    |
    [{box}{end_punctuation}{currency}{numeric}] [{lower_accented}]
    |
    # leave out [upper_accented][currency] without further info, because it's used in some
    # fancy leetspeak-esque writing
    [{lower_accented}{box}{end_punctuation}] [{currency}]
    |
    \s [{upper_accented}] [{currency}]
    |
    [{upper_accented}{box}{end_punctuation}] [{numeric}]
    |
    [{lower_accented}{upper_accented}{currency}{numeric}{box}] [{end_punctuation}] [{start_punctuation}]
    |
    [{currency}{numeric}{box}] [{start_punctuation}]
    |
    [a-z] [{upper_accented}] [{start_punctuation}{currency}]
    |
    [{box}] [{kaomoji}]
    |
    [{lower_accented}{upper_accented}{currency}{numeric}{start_punctuation}{end_punctuation}] [{box}]
    |
    [{box}] [{end_punctuation}]
    |
    [{lower_accented}{upper_accented}] [{end_punctuation}] \\w
    |

    # The ligature œ outside of English-looking words
    [Œœ][^a-z]
    |

    # Windows-1252 2-character mojibake that isn't covered by the cases above
    [ÂÃÎÐ][€Šš¢Ÿž\xa0\xad®©°·»{end_punctuation}–—´]
    |
    × [²³]
    |

    # Windows-1252 mojibake sequences for some South Asian alphabets
    à[²µ¹¼½¾]
    |

    # MacRoman mojibake that isn't covered by the cases above
    √[±∂†≠®™´≤≥¥µø]
    |
    ≈[°¢]
    |
    ‚Ä[ìîïòôúùû†°¢π]
    |
    ‚[âó][àä°ê]
    |

    # Windows-1251 mojibake of characters in the U+2000 range
    вЂ
    |

    # Windows-1251 mojibake of Latin-1 characters and/or the Cyrillic alphabet
    [ВГРС][{c1}{bad}{start_punctuation}{end_punctuation}{currency}°µ][ВГРС]
    |

    # Windows-1252 encodings of 'à' and 'á'
    Ã[\xa0¡]
    |
    [a-z]\\s?Ã[ ]
    |

    # Windows-1253 mojibake of characters in the U+2000 range
    β€[™\xa0Ά\xad®°]
    |
    
    # Windows-1253 mojibake of Latin-1 characters and/or the Greek alphabet
    [ΒΓΞΟ][{c1}{bad}{start_punctuation}{end_punctuation}{currency}°][ΒΓΞΟ]
""".format(**MOJIBAKE_CATEGORIES), re.VERBOSE)


def badness(text):
    """
    Get the 'badness' of a sequence of text. A badness greater than 0 indicates
    that some of it seems to be mojibake.
    """
    return len(BADNESS_RE.findall(text))


def is_bad(text):
    """
    Returns true iff the given text looks like it contains mojibake.
    """
    return bool(BADNESS_RE.search(text))


# Character classes that help us pinpoint embedded mojibake. These can
# include common characters, because we'll also check them for 'badness'.
UTF8_CLUES = {
    # Letters that decode to 0xC2 - 0xDF in a Latin-1-like encoding
    'utf8_first_of_2': (
        'ÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßĂĆČĎĐĘĚĞİĹŃŇŐŘŞŢŮŰ'
        'ΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩΪΫάέήίВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    ),
    # Letters that decode to 0xE0 - 0xEF in a Latin-1-like encoding
    'utf8_first_of_3': (
        'àáâãäåæçèéêëìíîïăćčďęěĺŕΰαβγδεζηθικλμνξοабвгдежзийклмноп'
    ),
    # Letters that decode to 0xF0 or 0xF3 in a Latin-1-like encoding.
    # (Other leading bytes correspond only to unassigned codepoints)
    'utf8_first_of_4': (
        'ðóđğπσру'
    ),
    # Letters that decode to 0x80 - 0xBF in a Latin-1-like encoding
    'utf8_continuation': (
        '\x80-\xbf'
        'ĄąĽľŁłŒœŚśŞşŠšŤťŸŹźŻżŽžƒˆˇ˘˛˜˝΄΅'
        'ΆΈΉΊΌΎΏЁЂЃЄЅІЇЈЉЊЋЌЎЏёђѓєѕіїјљњћќўџҐґ'
        '–—―‘’‚“”„†‡•…‰‹›€№™'
        ' '
    ),
}

# This regex uses UTF8_CLUES to find sequences of likely mojibake.
# It matches them with + so that several adjacent UTF-8-looking sequences
# get coalesced into one, allowing them to be fixed more efficiently
# and not requiring every individual subsequence to be detected as 'badness'.
UTF8_DETECTOR_RE = re.compile("""
    (
        [{utf8_first_of_2}] [{utf8_continuation}]
        |
        [{utf8_first_of_3}] [{utf8_continuation}]{{2}}
        |
        [{utf8_first_of_4}] [{utf8_continuation}]{{3}}
    )+
""".format(**UTF8_CLUES), re.VERBOSE)