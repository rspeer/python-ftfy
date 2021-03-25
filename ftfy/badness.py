"""
Heuristics to detect likely mojibake.
"""

import re
import warnings
from ftfy import chardata


def sequence_weirdness(text):
    warnings.warn(
        "`sequence_weirdness()` is an old heuristic, and the current "
        "closest equivalent is `ftfy.badness.badness()`"
    )
    return badness(text)


def badness(text):
    """
    Get the 'badness' of a sequence of text. A badness greater than 0 indicates
    that some of it seems to be mojibake.
    """
    return len(chardata.BADNESS_RE.findall(text))


def is_bad(text):
    """
    Returns true iff the given text looks like it contains mojibake.
    """
    return bool(chardata.BADNESS_RE.search(text))
