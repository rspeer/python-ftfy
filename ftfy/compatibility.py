"""
Makes some function names and behavior consistent between Python 2 and
Python 3, and also between narrow and wide builds.
"""
from __future__ import unicode_literals
import sys
import re
import unicodedata

if sys.hexversion >= 0x03000000:
    from html import entities
    unichr = chr
    xrange = range
    PYTHON2 = False
else:
    import htmlentitydefs as entities
    unichr = unichr
    xrange = xrange
    PYTHON2 = True
htmlentitydefs = entities

PYTHON34_OR_LATER = (sys.hexversion >= 0x03040000)


def _narrow_unichr_workaround(codepoint):
    """
    A replacement for unichr() on narrow builds of Python. This will get
    us the narrow representation of an astral character, which will be
    a string of length two, containing two UTF-16 surrogates.
    """
    escaped = b'\\U%08x' % codepoint
    return escaped.decode('unicode-escape')


if sys.maxunicode < 0x10000:
    unichr = _narrow_unichr_workaround
    # In a narrow build of Python, we can't write a regex involving astral
    # characters. If we want to write the regex:
    #
    #   [\U00100000-\U0010ffff]
    #
    # The actual string that defines it quietly turns into:
    #
    #   [\udbc0\udc00-\udbff\udfff]
    #
    # And now the range operator only applies to the middle two characters.
    # It looks like a range that's going backwards from \dc00 to \dbff,
    # which is an error.
    #
    # What we can do instead is rewrite the expression to be _about_ the two
    # surrogates that make up the astral characters, instead of the characters
    # themselves. This would be wrong on a wide build, but it works on a
    # narrow build.
    UNSAFE_PRIVATE_USE_RE = re.compile('[\udbc0-\udbff][\udc00-\udfff]')
else:
    UNSAFE_PRIVATE_USE_RE = re.compile('[\U00100000-\U0010ffff]')


def bytes_to_ints(bytestring):
    """
    No matter what version of Python this is, make a sequence of integers from
    a bytestring. On Python 3, this is easy, because a 'bytes' object _is_ a
    sequence of integers.
    """
    if PYTHON2:
        return [ord(b) for b in bytestring]
    else:
        return bytestring


def is_printable(char):
    """
    str.isprintable() is new in Python 3. It's useful in `explain_unicode`, so
    let's make a crude approximation in Python 2.
    """
    if PYTHON2:
        return not unicodedata.category(char).startswith('C')
    else:
        return char.isprintable()
