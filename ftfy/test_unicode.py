# -*- coding: utf-8 -*-
from ftfy.fixes import fix_text_encoding
import unicodedata

# Most single-character strings which have been misencoded should be restored.
def test_all_bmp_characters():
    for index in xrange(0xa0, 0xfffd):
        char = unichr(index)
        # Exclude code points that are not assigned
        if unicodedata.category(char) not in ('Co', 'Cn', 'Mc', 'Mn'):
            garble = char.encode('utf-8').decode('latin-1')
            assert fix_text_encoding(garble) == char

phrases = [
    u"\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    u"\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    u"\u2039ALLÍ ESTÁ\u203A",
    u"\u2014ALLÍ ESTÁ\u2014",
    u"AHÅ™, the new sofa from IKEA®",
    #u"\u2014a radius of 10 Å\u2014",
]
# These phrases should not be erroneously "fixed"
def test_valid_phrases():
    for phrase in phrases:
        print phrase
        yield check_phrase, phrase
        # make it not just confirm based on the opening punctuation
        yield check_phrase, phrase[1:]

def check_phrase(text):
    assert fix_text_encoding(text) == text, text

