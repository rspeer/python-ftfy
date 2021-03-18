"""
Heuristics to detect likely mojibake.
"""

import re

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
    [{upper_accented}{lower_accented}{box}{end_punctuation}] [{currency}]
    |
    [{upper_accented}{box}{end_punctuation}] [{numeric}]
    |
    [{lower_accented}{upper_accented}{currency}{numeric}{box}] [{end_punctuation}] [{start_punctuation}]
    |
    [{currency}{numeric}{box}] [{start_punctuation}]
    |
    [a-z] [{upper_accented}] [{start_punctuation}]
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
    [ÂÃÎÐ][€Šš¢Ÿž\xa0\xad®°·»{end_punctuation}–—´]
    |
    × [{end_punctuation}²³]
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

    # Windows-1252 encodings of 'à'
    Ã\xa0
    |
    [a-z]\\s?Ã[ ]
    |

    # Windows-1253 mojibake of characters in the U+2000 range
    β€[™\xa0Ά\xad®°]
    |
    
    # Windows-1253 mojibake of Latin-1 characters and/or the Greek alphabet
    [ΒΓΞΟ][{c1}{bad}{start_punctuation}{end_punctuation}{currency}°][ΒΓΞΟ]

    # TODO: add longer sequences that detect Windows-1251 and Windows-1253
    # two-character mojibake in groups, because the two characters alone
    # aren't enough information

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
