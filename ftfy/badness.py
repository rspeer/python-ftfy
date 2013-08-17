# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.chardata import CATEGORY_RANGES
import re

def _make_weirdness_regex():
    """
    Creates a list of regexes that match 'weird' character sequences.
    The more matches there are, the weirder the text is.
    """
    groups = []

    # Match lowercase letters that are followed by non-ASCII uppercase letters
    groups.append(u'([{Ll}][{Lun}{Lt}])'.format(**CATEGORY_RANGES))

    # Match diacritic marks, except when they modify a non-cased letter.
    #
    # You wouldn't put a diacritic mark on a digit or a space, for example.
    # You might, of course, put diacritics on Latin letters, but in that case
    # it's a lot more common to see the pre-combined version. Modifier
    # characters are most often used in other scripts where the letters have
    # category 'Lo'.
    groups.append(u'([^{Lo}][{Mn}{Mc}{Me}])'.format(**CATEGORY_RANGES))

    # Match non-Latin characters adjacent to Latin characters.
    #
    # This is a simplification from ftfy version 2, which compared all
    # adjacent scripts. However, the ambiguities we need to resolve come from
    # encodings designed to represent Latin characters.
    groups.append(u'([{latin}][{nonlatin}])'.format(**CATEGORY_RANGES))
    groups.append(u'([{nonlatin}][{latin}])'.format(**CATEGORY_RANGES))

    # Match C1 control characters, which are almost always the result of
    # decoding Latin-1 that was meant to be Windows-1252.
    groups.append(u'([\x80-\x9f])')

    # Match adjacent characters from any different pair of these categories:
    # - Letter modifiers (Lm)
    # - Spacing combining marks (Mc)
    # - Enclosing marks (Me)
    # - Nonspacing marks (Mn)
    # - Miscellaneous numbers (No)
    # - Symbol modifiers (Sk)
    # - Mathematical symbols (Sm)
    # - Currency symbols (Sc)
    # - Other symbols (So)
    exclusive_categories = ['Lm', 'Mc', 'Me', 'Mn', 'No', 'Sk', 'Sm', 'Sc', 'So']
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
    Determine how often a text has unexpected characters or sequences of
    characters. This metric is used to disambiguate when text should be
    re-decoded or left as is.
    """
    return len(WEIRDNESS_RE.findall(text))


def better_text(newtext, oldtext):
    return text_cost(newtext) < text_cost(oldtext)


def text_cost(text):
    return sequence_weirdness(text) * 2 + len(text)
