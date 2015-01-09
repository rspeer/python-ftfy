# -*- coding: utf-8 -*-
from ftfy.fixes import fix_text_encoding, fix_encoding_and_explain, apply_plan, possible_encoding, fix_surrogates
from ftfy.badness import ENDING_PUNCT_RE
import unicodedata
import sys
from nose.tools import eq_

if sys.hexversion >= 0x03000000:
    unichr = chr


def char_names(text):
    """
    Show the names of the characters involved. Helpful for debugging when
    characters themselves are not visually distinguishable.
    """
    return [unicodedata.name(c) for c in text]


# Most single-character strings which have been misencoded should be restored.
def test_all_bmp_characters():
    for index in range(0xa0, 0xfffd):
        char = unichr(index)
        # Exclude code points that are not assigned
        if unicodedata.category(char) not in ('Co', 'Cn', 'Cs', 'Mc', 'Mn'):
            garble = char.encode('utf-8').decode('latin-1')
            if not (index < 0x800 and ENDING_PUNCT_RE.search(garble)):
                garble2 = char.encode('utf-8').decode('latin-1').encode('utf-8').decode('latin-1')
                for garb in (garble, garble2):
                    fixed, plan = fix_encoding_and_explain(garb)
                    eq_(fixed, char)
                    eq_(apply_plan(garb, plan), char)


phrases = [
    u"\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    u"\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    u"\u2039ALLÍ ESTÁ\u203A",
    u"\u2014ALLÍ ESTÁ\u2014",
    u"AHÅ™, the new sofa from IKEA®",
    u"ВІКІ is Ukrainian for WIKI",
    #u"\u2014a radius of 10 Å\u2014",
]
# These phrases should not be erroneously "fixed"
def test_valid_phrases():
    for phrase in phrases:
        yield check_phrase, phrase


def check_phrase(text):
    eq_(fix_text_encoding(text), text)
    eq_(fix_text_encoding(text.encode('utf-8').decode('latin-1')), text)
    # make sure that the opening punctuation is not the only thing that makes
    # it work
    eq_(fix_text_encoding(text[1:]), text[1:])
    eq_(fix_text_encoding(text[1:].encode('utf-8').decode('latin-1')), text[1:])


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, 'latin-1')


def test_fix_with_backslash():
    eq_(fix_text_encoding(u"<40\\% vs \xe2\x89\xa540\\%"), u"<40\\% vs ≥40\\%")


if __name__ == '__main__':
    test_all_bmp_characters()
