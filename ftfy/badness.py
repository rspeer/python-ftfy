# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from ftfy.chardata import (SCRIPT_MAP, SINGLE_BYTE_WEIRDNESS,
    WINDOWS_1252_GREMLINS)

import sys
if sys.hexversion >= 0x03000000:
    unichr = chr

CONSISTENT_SCRIPTS_RE = re.compile(r'([A-Za-z])(\1+)')
LETTER_SEGMENTS_RE = re.compile(r'([A-Za-z]+)')
LOWERCASE_RE = re.compile(r'([a-z])')
DOUBLE_WEIRD_RE = re.compile(r'(WW+)')
GREMLINS_RE = re.compile('[' +
    ''.join([unichr(codepoint) for codepoint in WINDOWS_1252_GREMLINS])
    + ']')

WEIRD_CHARACTER_RES = []
for i in range(5):
    chars = [unichr(codepoint) for codepoint in range(0x80, 0x100)
             if SINGLE_BYTE_WEIRDNESS[codepoint] > i]
    WEIRD_CHARACTER_RES.append(re.compile('[' + ''.join(chars) + ']'))

def num_consistent_scripts(scriptdata):
    """
    Count the number of times two adjacent letters are in the same script.

    Uses a "scriptdata" string as input, not the actual text.

    >>> num_consistent_scripts('LL AAA.')
    3
    >>> num_consistent_scripts('LLAAA ...')
    3
    >>> num_consistent_scripts('LAL')
    0
    >>> num_consistent_scripts('..LLL..')
    2
    >>> num_consistent_scripts('LWWW')
    2
    """
    matches = CONSISTENT_SCRIPTS_RE.findall(scriptdata)
    total = 0
    for first, rest in matches:
        total += len(rest)
    return total


def num_inconsistent_scripts(scriptdata):
    """
    Count the number of times two adjacent letters are in different scripts,
    or are both marked as 'weird'.

    Uses a "scriptdata" string as input, not the actual text.

    >>> num_inconsistent_scripts('LL AAA.')
    0
    >>> num_inconsistent_scripts('LLAAA ...')
    1
    >>> num_inconsistent_scripts('LAL')
    2
    >>> num_inconsistent_scripts('..LLL..')
    0
    >>> num_inconsistent_scripts('LWWW')
    3
    """
    # First, count the number of times two letters are adjacent
    letter_segments = LETTER_SEGMENTS_RE.findall(scriptdata)
    adjacent_letters = 0
    for seg in letter_segments:
        adjacent_letters += len(seg) - 1

    # Then subtract out the number of times the scripts are consistent,
    # but first add back in adjacent weird characters
    double_weird_segments = DOUBLE_WEIRD_RE.findall(scriptdata)
    for seg in double_weird_segments:
        adjacent_letters += len(seg) - 1

    return adjacent_letters - num_consistent_scripts(scriptdata)


def script_obscurity(scriptdata):
    """
    Count the number of characters in obscure scripts. Characters in very
    obscure scripts count twice as much.

    >>> script_obscurity('LWWW')
    0
    >>> script_obscurity('Llkzz')
    6
    """
    return len(LOWERCASE_RE.findall(scriptdata)) + scriptdata.count('z')


def character_weirdness(text):
    """
    Sum the weirdness of all the single-byte characters in this text.

    >>> character_weirdness('test')
    0
    >>> character_weirdness('wúút')
    0
    >>> character_weirdness('\x81\x81')
    10
    """
    total = 0
    for weird_re in WEIRD_CHARACTER_RES:
        found = weird_re.findall(text)
        total += len(found)
    return total


def text_badness(text):
    """
    Count the total badness of a string, which helps to determine when an
    encoding has gone wrong.

    Obvious problems (badness = 100):
    - The replacement character \ufffd, indicating a decoding error
    - Unassigned or private-use Unicode characters

    Very weird things (badness = 10):
    - Adjacent letters from two different scripts
    - Letters adjacent to obscure single-byte symbols
    - Obscure single-byte symbols adjacent to each other
    - Improbable control characters, such as 0x81

    Moderately weird things:
    - Improbable single-byte characters, such as ƒ or ¬
    - Letters in somewhat rare scripts (they'll still probably look better than
      they would in the wrong encoding)
    """
    scriptdata = text.translate(SCRIPT_MAP)
    badness = character_weirdness(text) + script_obscurity(scriptdata)
    badness += 10 * num_inconsistent_scripts(scriptdata)
    badness += 100 * scriptdata.count('?')
    return badness
