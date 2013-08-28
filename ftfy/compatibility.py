"""
Makes some function names and behavior consistent between Python 2 and
Python 3, and also between narrow and wide builds.
"""
import sys

if sys.hexversion >= 0x03000000:
    from html import entities
    htmlentitydefs = entities
    unichr = chr
    xrange = range
    PYTHON2 = False
else:
    import htmlentitydefs
    unichr = unichr
    xrange = xrange
    PYTHON2 = True


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
