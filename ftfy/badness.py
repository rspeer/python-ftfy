# -*- coding: utf-8 -*-
"""
Heuristics to determine whether re-encoding text is actually making it
more reasonable.
"""

from __future__ import unicode_literals
from ftfy.chardata import chars_to_classes
import re
import unicodedata

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
# 0 = Math symbol (Sm)
# 1 = Currency symbol (Sc)
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

    # Match lowercase letters that are followed by non-ASCII uppercase letters
    groups.append('lA')

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

    # Match C1 control characters, which are almost always the result of
    # decoding Latin-1 that was meant to be Windows-1252.
    groups.append(u'X')

    # Match adjacent characters from any different pair of these categories:
    # - Modifier marks (M)
    # - Letter modifiers (m)
    # - Miscellaneous numbers (N)
    # - Symbols (0123)

    exclusive_categories = 'MmN0123'
    for cat1 in exclusive_categories:
        others_range = ''.join(c for c in exclusive_categories if c != cat1)
        groups.append('{cat1}[{others_range}]'.format(
            cat1=cat1, others_range=others_range
        ))
    regex = '|'.join('({0})'.format(group) for group in groups)
    return re.compile(regex)

WEIRDNESS_RE = _make_weirdness_regex()


def sequence_weirdness(text):
    """
    Determine how often a text has unexpected characters or sequences of
    characters. This metric is used to disambiguate when text should be
    re-decoded or left as is.

    We start by normalizing text in NFC form, so that penalties for
    diacritical marks don't apply to characters that know what to do with
    them.
    """
    text2 = unicodedata.normalize('NFC', text)
    return len(WEIRDNESS_RE.findall(chars_to_classes(text2)))


def better_text(newtext, oldtext):
    """
    Is newtext better than oldtext?
    """
    return text_cost(newtext) < text_cost(oldtext)


def text_cost(text):
    """
    An overall cost function for text. All else being equal, shorter strings
    are better.
    """
    return sequence_weirdness(text) * 2 + len(text)

