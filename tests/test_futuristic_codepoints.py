from ftfy.fixes import fix_encoding
from ftfy.badness import sequence_weirdness
import sys
from nose.tools import eq_


def test_unknown_emoji():
    # The range we accept as emoji has gotten larger. Let's make sure we can
    # decode the futuristic emoji U+1F960, which will probably be a picture of
    # a fortune cookie in Unicode 10.0:
    emoji_text = "\U0001f960 I see emoji in your future"
    emojibake = emoji_text.encode('utf-8').decode('windows-1252')
    eq_(fix_encoding(emojibake), emoji_text)

    # We believe enough in the future of this codepoint that we'll even
    # recognize it with a mangled byte A0
    emojibake = emojibake.replace('\xa0', ' ')
    eq_(fix_encoding(emojibake), emoji_text)

    # Increment the first byte to get a very similar test case, but a
    # codepoint that will definitely not exist anytime soon. In this case,
    # we consider the existing text, "ñŸ¥\xa0", to be more probable.
    not_emoji = "\U0005f960 I see mojibake in your present".encode('utf-8').decode('windows-1252')
    eq_(fix_encoding(not_emoji), not_emoji)


def test_unicode_9():
    # This string is 'bɪg'.upper() in Python 3.6 or later, containing the
    # new codepoint U+A7AE LATIN CAPITAL LETTER SMALL CAPITAL I.
    eq_(sequence_weirdness("BꞮG"), 0)

    # That should be less weird than having a definitely-unassigned character
    # in the string.
    eq_(sequence_weirdness("B\U00090000G"), 2)

