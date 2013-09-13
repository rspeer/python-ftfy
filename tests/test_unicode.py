# -*- coding: utf-8 -*-
from ftfy.fixes import fix_text_encoding, fix_text_and_explain
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
            garble2 = char.encode('utf-8').decode('latin-1').encode('utf-8').decode('latin-1')
            eq_(char_names(fix_text_encoding(garble)), char_names(char), fix_text_and_explain(garble))
            eq_(char_names(fix_text_encoding(garble2)), char_names(char))

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
        # make it not just confirm based on the opening punctuation
        yield check_phrase, phrase[1:]

def check_phrase(text):
    eq_(fix_text_encoding(text), text)
    eq_(fix_text_encoding(text.encode('utf-8').decode('latin-1')), text)

if __name__ == '__main__':
    test_all_bmp_characters()

