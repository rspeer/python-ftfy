"""
Heuristics to detect likely mojibake.
"""

import re
from .chardata import badness


def sequence_weirdness(text):
    # TODO: do the deprecation thing
    return badness(text)
