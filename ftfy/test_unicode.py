# -*- coding: utf-8 -*-
from ftfy import fix_bad_encoding
import unicodedata
import sys

if sys.hexversion >= 0x03000000:
    xrange = range
    unichr = chr

# Most single-character strings which have been misencoded should be restored.
def test_all_bmp_characters():
    for index in xrange(0xa0, 0xfffd):
        char = unichr(index)
        # Exclude code points that are not assigned
        if unicodedata.category(char) not in ('Co', 'Cn'):
            garble = char.encode('utf-8').decode('latin-1')
            assert fix_bad_encoding(garble) == char

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
        yield check_phrase, phrase
        # make it not just confirm based on the opening punctuation
        yield check_phrase, phrase[1:]

def check_phrase(text):
    assert fix_bad_encoding(text) == text, text

