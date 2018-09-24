from ftfy.fixes import fix_encoding
from ftfy.badness import sequence_weirdness
import sys


def test_unknown_emoji():
    # The range we accept as emoji has gotten larger. Let's make sure we can
    # decode the futuristic emoji U+1F960, which will probably be a picture of
    # a fortune cookie in Unicode 10.0:
    emoji_text = "\U0001f960 I see emoji in your future"
    emojibake = emoji_text.encode('utf-8').decode('windows-1252')
    assert fix_encoding(emojibake) == emoji_text

    # We believe enough in the future of this codepoint that we'll even
    # recognize it with a mangled byte A0
    emojibake = emojibake.replace('\xa0', ' ')
    assert fix_encoding(emojibake) == emoji_text

    # Increment the first byte to get a very similar test case, but a
    # codepoint that will definitely not exist anytime soon. In this case,
    # we consider the existing text, "ñŸ¥\xa0", to be more probable.
    not_emoji = "\U0005f960 I see mojibake in your present".encode('utf-8').decode('windows-1252')
    assert fix_encoding(not_emoji) == not_emoji


def test_unicode_9():
    # This string is 'bɪg'.upper() in Python 3.6 or later, containing the
    # new codepoint U+A7AE LATIN CAPITAL LETTER SMALL CAPITAL I.
    assert sequence_weirdness("BꞮG") == 0

    # That should be less weird than having a definitely-unassigned character
    # in the string.
    assert sequence_weirdness("B\U00090000G") == 2


def test_unicode_10():
    # This string is the word "thalīṃ" in the Zanabazar Square Script,
    # a script added in Unicode 10. These characters are recognized as being
    # assigned by Python 3.7, and therefore ftfy should recognize them on
    # all versions for consistency.
    thalim = "\U00011A1A\U00011A2C\U00011A01\U00011A38"
    assert sequence_weirdness(thalim) == 0


def test_unicode_11():
    # Unicode 11 has implemented the mtavruli form of the Georgian script.
    # They are analogous to capital letters in that they can be used to
    # emphasize text or write a headline.
    #
    # Python will convert to that form when running .upper() on Georgian text,
    # starting in version 3.7.0. We want to recognize the result as reasonable
    # text on all versions.
    #
    # This text is the mtavruli form of "ქართული ენა", meaning "Georgian
    # language".

    georgian_mtavruli_text = 'ᲥᲐᲠᲗᲣᲚᲘ ᲔᲜᲐ'
    assert sequence_weirdness(georgian_mtavruli_text) == 0

    mojibake = georgian_mtavruli_text.encode('utf-8').decode('sloppy-windows-1252')
    assert fix_encoding(mojibake) == georgian_mtavruli_text
