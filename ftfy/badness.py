"""
Heuristics to determine whether re-encoding text is actually making it
more reasonable.
"""

import re
import unicodedata

from ftfy.chardata import chars_to_classes

# The following regex uses the mapping of character classes to ASCII
# characters defined in chardata.py and build_data.py:
#
# L = Latin capital letter
# l = Latin lowercase letter
# A = Non-latin capital or title-case letter
# a = Non-latin lowercase letter
# C = Non-cased letter (Lo)
# X = Control character (Cc)
# m = Letter modifier (Lm)
# M = Mark (Mc, Me, Mn)
# N = Miscellaneous numbers (No)
# 1 = Math symbol (Sm) or currency symbol (Sc)
# 2 = Symbol modifier (Sk)
# 3 = Other symbol (So)
# S = UTF-16 surrogate
# _ = Unassigned character
#   = Whitespace
# o = Other


def _make_weirdness_regex():
    """
    Creates a list of regexes that match 'weird' character sequences.
    The more matches there are, the weirder the text is.
    """
    groups = []

    # Match diacritical marks, except when they modify a non-cased letter or
    # another mark.
    #
    # You wouldn't put a diacritical mark on a digit or a space, for example.
    # You might put it on a Latin letter, but in that case there will almost
    # always be a pre-composed version, and we normalize to pre-composed
    # versions first. The cases that can't be pre-composed tend to be in
    # large scripts without case, which are in class C.
    groups.append('[^CM]M')

    # Match non-Latin characters adjacent to Latin characters.
    #
    # This is a simplification from ftfy version 2, which compared all
    # adjacent scripts. However, the ambiguities we need to resolve come from
    # encodings designed to represent Latin characters.
    groups.append('[Ll][AaC]')
    groups.append('[AaC][Ll]')

    # Match IPA letters next to capital letters.
    #
    # IPA uses lowercase letters only. Some accented capital letters next to
    # punctuation can accidentally decode as IPA letters, and an IPA letter
    # appearing next to a capital letter is a good sign that this happened.
    groups.append('[LA]i')
    groups.append('i[LA]')

    # Match non-combining diacritics. We've already set aside the common ones
    # like ^ (the CIRCUMFLEX ACCENT, repurposed as a caret, exponent sign,
    # or happy eye) and assigned them to category 'o'. The remaining ones,
    # like the diaeresis (¨), are pretty weird to see on their own instead
    # of combined with a letter.
    groups.append('2')

    # Match C1 control characters, which are almost always the result of
    # decoding Latin-1 that was meant to be Windows-1252.
    groups.append('X')

    # Match private use and unassigned characters.
    groups.append('P')
    groups.append('_')

    # Match adjacent characters from any different pair of these categories:
    # - Modifier marks (M)
    # - Letter modifiers (m)
    # - Miscellaneous numbers (N)
    # - Symbols (1 or 3, because 2 is already weird on its own)

    exclusive_categories = 'MmN13'
    for cat1 in exclusive_categories:
        others_range = ''.join(c for c in exclusive_categories if c != cat1)
        groups.append(
            '{cat1}[{others_range}]'.format(cat1=cat1, others_range=others_range)
        )
    regex = '|'.join(groups)
    return re.compile(regex)


WEIRDNESS_RE = _make_weirdness_regex()

# These characters appear in mojibake but also appear commonly on their own.
# We have a slight preference to leave them alone.
COMMON_SYMBOL_RE = re.compile(
    '['
    '\N{HORIZONTAL ELLIPSIS}\N{EM DASH}\N{EN DASH}'
    '\N{LEFT SINGLE QUOTATION MARK}\N{LEFT DOUBLE QUOTATION MARK}'
    '\N{RIGHT SINGLE QUOTATION MARK}\N{RIGHT DOUBLE QUOTATION MARK}'
    '\N{INVERTED EXCLAMATION MARK}\N{INVERTED QUESTION MARK}\N{DEGREE SIGN}'
    '\N{TRADE MARK SIGN}'
    '\N{REGISTERED SIGN}'
    '\N{SINGLE LEFT-POINTING ANGLE QUOTATION MARK}'
    '\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}'
    '\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}'
    '\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}'
    '\N{NO-BREAK SPACE}'
    '\N{ACUTE ACCENT}\N{MULTIPLICATION SIGN}\N{LATIN SMALL LETTER SHARP S}'
    '\ufeff'  # The byte-order mark, whose encoding 'ï»¿' looks common
    ']'
)

# These are sequences that are common mojibake, resulting from common encodings
# that are mixed up with UTF-8 on characters from their own character map.
#
# Sequences that match this regex will increase the `sequence_weirdness` of a
# string.
#
# This helps to strengthen evidence that text should be fixed in a way that's
# separate from the character classes above, or to counter COMMON_SYMBOL_RE's
# fondness for characters such as inverted exclamation marks and multiplication
# signs in contexts where they really do look like mojibake.

MOJIBAKE_SYMBOL_RE = re.compile(
    # The codepoints of decoded characters these correspond to are as follows:
    #
    #   Initial char.   Codepoints  What's in this range
    #   -------------   ----------  --------------------
    #   Â               80..BF      Latin-1 control characters and symbols
    #   Ã, Ă            C0..FF      Latin-1 accented letters
    #   Î               380..3BF    Greek letters
    #   Ï, Ď            3C0..3FF    Greek letters
    #   Ð, Đ            400..43F    Cyrillic letters
    #   Ñ, Ń            440..47F    Cyrillic letters
    #   Ø, Ř            600..63F    Arabic letters
    #   Ù, Ů            640..67F    Arabic letters
    #
    # Here, we leave out Hebrew letters (which have a separate heuristic), and
    # the rarer letters from each alphabet. This regex doesn't have to contain
    # every character we want to decode -- just the sequences that we want to
    # specifically detect as 'this looks like mojibake'.
    # 
    # We avoid ranges whose mojibake starts with characters like Ó -- which
    # maps to Armenian and some more Cyrillic letters -- because those could be
    # the 'eyes' of kaomoji faces.
    #
    # The set of possible second characters covers most of the possible symbols
    # that would be the second byte of UTF-8 mojibake. It is limited to the
    # ones that are unlikely to have a real meaning when following one of these
    # capital letters, and appear as the second character in Latin-1,
    # Windows-1250, or Windows-1252 mojibake.
    '[ÂÃÎÏÐÑØÙĂĎĐŃŘŮ][\x80-\x9f€ƒ‚„†‡ˆ‰‹Œ“•˜œŸ¡¢£¤¥¦§¨ª«¬¯°±²³µ¶·¸¹º¼½¾¿ˇ˘˝]|'
    
    # Character sequences we have to be a little more cautious about if they're
    # at the end of a word, but are totally okay to fix in the middle
    r'[ÂÃÎÏÐÑØÙĂĎĐŃŘŮ][›»‘”´©™]\w|'

    # Most Hebrew letters get mojibaked to two-character sequences that start with
    # the multiplication sign. In the list of following characters, we exclude
    # currency symbols and numbers, which might actually be intended to be
    # multiplied. We also exclude characters like ¶ which, although they don't
    # make sense after a multiplication sign, wouldn't decode to an existing
    # Hebrew letter if they were mojibake.
    '×[\x80-\x9fƒ‚„†‡ˆ‰‹Œ“•˜œŸ¡¦§¨ª«¬¯°²³ˇ˘›‘”´©™]|'
    
    # Similar mojibake of low-numbered characters in MacRoman. Leaving out
    # most mathy characters because of false positives, but cautiously catching
    # "√±" (mojibake for "ñ") and "√∂" (mojibake for "ö") in the middle of a
    # word.
    #
    # I guess you could almost have "a√±b" in math, except that's not where
    # you'd want the ±. Complex numbers don't quite work that way. "√±" appears
    # unattested in equations in my Common Crawl sample.
    #
    # Also left out eye-like letters, including accented o's, for when ¬ is
    # the nose of a kaomoji.
    '[¬√][ÄÅÇÉÑÖÜáàâäãåçéèêëíìîïñúùûü†¢£§¶ß®©™≠ÆØ¥ªæø≤≥]|'
    r'\w√[±∂]\w|'

    # MacRoman mojibake of Hebrew involves a diamond character that is
    # uncommon in intended text.
    '◊|'
    
    # ISO-8859-1, ISO-8859-2, or Windows-1252 mojibake of characters U+10000
    # to U+1FFFF. (The Windows-1250 and Windows-1251 versions might be too
    # plausible.)
    '[ðđ][Ÿ\x9f]|'
    
    # Windows-1252 or Windows-1250 mojibake of Windows punctuation characters
    'â€|'
    
    # Windows-1251 mojibake of some Windows punctuation characters
    'вЂ[љћ¦°№™ќ“”]'
)


def sequence_weirdness(text):
    """
    Determine how often a text has unexpected characters or sequences of
    characters. This metric is used to disambiguate when text should be
    re-decoded or left as is.

    We start by normalizing text in NFC form, so that penalties for
    diacritical marks don't apply to characters that know what to do with
    them.

    The following things are deemed weird:

    - Lowercase letters followed by non-ASCII uppercase letters
    - Non-Latin characters next to Latin characters
    - Un-combined diacritical marks, unless they're stacking on non-alphabetic
      characters (in languages that do that kind of thing a lot) or other
      marks
    - C1 control characters
    - Adjacent symbols from any different pair of these categories:

        - Modifier marks
        - Letter modifiers
        - Non-digit numbers
        - Symbols (including math and currency)

    The return value is the number of instances of weirdness.
    """
    text2 = unicodedata.normalize('NFC', text)
    weirdness = len(WEIRDNESS_RE.findall(chars_to_classes(text2)))
    adjustment = len(MOJIBAKE_SYMBOL_RE.findall(text2)) * 2 - len(
        COMMON_SYMBOL_RE.findall(text2)
    )
    return weirdness * 2 + adjustment


def text_cost(text):
    """
    An overall cost function for text. Weirder is worse, but all else being
    equal, shorter strings are better.

    The overall cost is measured as the "weirdness" (see
    :func:`sequence_weirdness`) plus the length.
    """
    return sequence_weirdness(text) + len(text)
