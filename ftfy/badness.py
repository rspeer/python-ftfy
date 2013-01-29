# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unicodedata
import re
from ftfy.chardata import (SCRIPT_LETTERS, SINGLE_BYTE_WEIRDNESS,
    WINDOWS_1252_GREMLINS)

import logging
LOG = logging.getLogger(__name__)
logging.basicConfig()

SCRIPT_MAP = {}

# Create a fast mapping that converts a Unicode string to a string describing
# its character classes, particularly the scripts its letters are in.
#
# Capital letters represent groups of commonly-used scripts.
# Lowercase letters represent rare scripts.
# . represents non-letters.
# Whitespace represents whitespace.
# ? represents errors.
#
# Astral characters pass through unmodified; we don't count them as script
# conflicts. They are probably intentional.

for codepoint in xrange(0x10000):
    char = unichr(codepoint)
    if unicodedata.category(char).startswith('L'):
        name = unicodedata.name(char)
        script = name.split()[0]
        if script in SCRIPT_LETTERS:
            SCRIPT_MAP[codepoint] = unicode(SCRIPT_LETTERS[script])
        else:
            SCRIPT_MAP[codepoint] = 'z'
    elif unicodedata.category(char).startswith('Z'):
        SCRIPT_MAP[codepoint] = ' '
    elif unicodedata.category(char) in ('Cn', 'Co'):
        SCRIPT_MAP[codepoint] = '?'
    else:
        SCRIPT_MAP[codepoint] = '.'

SCRIPT_MAP[0x09] = ' '
SCRIPT_MAP[0x0a] = '\n'
SCRIPT_MAP[0xfffd] = '?'

# mark weird extended characters as their own script
for codepoint in xrange(0x100):
    if SINGLE_BYTE_WEIRDNESS[codepoint] >= 2:
        SCRIPT_MAP[codepoint] = 'W'

CONSISTENT_SCRIPTS_RE = re.compile(r'([A-Za-z])(\1+)')
LETTER_SEGMENTS_RE = re.compile(r'([A-Za-z]+)')
LOWERCASE_RE = re.compile(r'([a-z])')
DOUBLE_WEIRD_RE = re.compile(r'(WW+)')
GREMLINS_RE = re.compile('[' +
    ''.join([unichr(codepoint) for codepoint in WINDOWS_1252_GREMLINS])
    + ']')

WEIRD_CHARACTER_RES = []
for i in xrange(5):
    chars = [unichr(codepoint) for codepoint in range(0x80, 0x100)
             if SINGLE_BYTE_WEIRDNESS[codepoint] > i]
    WEIRD_CHARACTER_RES.append(re.compile(u'[' + u''.join(chars) + u']'))


def num_consistent_scripts(scriptdata):
    """
    Count the number of times two adjacent letters are in the same script.

    Uses a "scriptdata" string as input, not the actual text.

    >>> num_consistent_scripts(u'LL AAA.')
    3
    >>> num_consistent_scripts(u'LLAAA ...')
    3
    >>> num_consistent_scripts(u'LAL')
    0
    >>> num_consistent_scripts(u'..LLL..')
    2
    >>> num_consistent_scripts(u'LWWW')
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

    >>> num_inconsistent_scripts(u'LL AAA.')
    0
    >>> num_inconsistent_scripts(u'LLAAA ...')
    1
    >>> num_inconsistent_scripts(u'LAL')
    2
    >>> num_inconsistent_scripts(u'..LLL..')
    0
    >>> num_inconsistent_scripts(u'LWWW')
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

    >>> script_obscurity(u'LWWW')
    0
    >>> script_obscurity(u'Llkzz')
    6
    """
    return len(LOWERCASE_RE.findall(scriptdata)) + scriptdata.count('z')


def character_weirdness(text):
    """
    Sum the weirdness of all the single-byte characters in this text.

    >>> character_weirdness(u'test')
    0
    >>> character_weirdness(u'wúút')
    0
    >>> character_weirdness(u'\x81\x81')
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
    badness += 100 * scriptdata.count(u'?')
    LOG.info('%r has badness %r' % (text, badness))
    return badness
