# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.chardata import CATEGORY_RANGES
import re

def _make_weirdness_regex():
    groups = []
    groups.append(u'([{Ll}][{Lu}{Lo}{Lt}])'.format(**CATEGORY_RANGES))
    groups.append(u'([{Mn}{Mc}])'.format(**CATEGORY_RANGES))
    exclusive_categories = ['Lm', 'Sk', 'Sm', 'Sc', 'No', 'So']
    for cat1 in exclusive_categories:
        others = exclusive_categories[:]
        others.remove(cat1)
        cat1_range = CATEGORY_RANGES[cat1]
        others_range = u''.join([CATEGORY_RANGES[other] for other in others])
        groups.append(
            u'([{cat1_range}][{others_range}])'.format(
                cat1_range=cat1_range,
                others_range=others_range
            )
        )
    regex = '|'.join(groups)
    return re.compile(regex)

WEIRDNESS_RE = _make_weirdness_regex()


def sequence_weirdness(text):
    """
    TODO: better documentation

    Determine how often a text has unexpected sequences of characters,
    which might indicate an incorrect encoding.
    """
    return len(WEIRDNESS_RE.findall(text))


def better_text(newtext, oldtext):
    return text_cost(newtext) < text_cost(oldtext)


def text_cost(text):
    return sequence_weirdness(text) * 2 + len(text)
