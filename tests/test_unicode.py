# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.fixes import fix_encoding, fix_encoding_and_explain, apply_plan, possible_encoding, fix_surrogates
from ftfy.badness import sequence_weirdness
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
def test_bmp_characters():
    for index in range(0xa0, 0xfffd):
        char = unichr(index)
        # Exclude code points that are not assigned
        if unicodedata.category(char) not in ('Co', 'Cn', 'Cs', 'Mc', 'Mn'):
            garble = char.encode('utf-8').decode('latin-1')
            # Exclude characters whose re-encoding is protected by the
            # 'sequence_weirdness' metric
            if sequence_weirdness(garble) >= 0:
                garble2 = char.encode('utf-8').decode('latin-1').encode('utf-8').decode('latin-1')
                for garb in (garble, garble2):
                    fixed, plan = fix_encoding_and_explain(garb)
                    eq_(fixed, char)
                    eq_(apply_plan(garb, plan), char)


phrases = [
    "\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    "\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    "\u2039ALLÍ ESTÁ\u203A",
    "\u2014ALLÍ ESTÁ\u2014",
    "AHÅ™, the new sofa from IKEA®",
    "ВІКІ is Ukrainian for WIKI",
    #"\u2014a radius of 10 Å\u2014",
]
# These phrases should not be erroneously "fixed"
def test_valid_phrases():
    for phrase in phrases:
        yield check_phrase, phrase


def check_phrase(text):
    eq_(fix_encoding(text), text)
    eq_(fix_encoding(text.encode('utf-8').decode('latin-1')), text)
    # make sure that the opening punctuation is not the only thing that makes
    # it work
    eq_(fix_encoding(text[1:]), text[1:])
    eq_(fix_encoding(text[1:].encode('utf-8').decode('latin-1')), text[1:])


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, 'latin-1')


def test_fix_with_backslash():
    eq_(fix_encoding("<40\\% vs \xe2\x89\xa540\\%"), "<40\\% vs ≥40\\%")


def test_mixed_utf8():
    eq_(fix_encoding('\xe2\x80\x9cmismatched quotes\x85\x94'), '“mismatched quotes…”')
    eq_(fix_encoding('â€œmismatched quotesâ€¦”'), '“mismatched quotes…”')


def test_surrogates():
    eq_(fix_surrogates('\udbff\udfff'), '\U0010ffff')
    eq_(fix_surrogates('\ud800\udc00'), '\U00010000')


if __name__ == '__main__':
    test_all_bmp_characters()
