# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.fixes import fix_encoding
import sys
from nose.tools import eq_

if sys.hexversion >= 0x03000000:
    unichr = chr


phrases = [
    "\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    "\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
    "\u2039ALLÍ ESTÁ\u203A",
    "\u2014ALLÍ ESTÁ\u2014",
    "AHÅ™, the new sofa from IKEA®",
    "ВІКІ is Ukrainian for WIKI",
    'These control characters \x1a are apparently intentional \x81',
    "I don't know what this is \x1a but this is the euro sign €",
    "\u2014a radius of 10 Å\u2014",
]
# These phrases should not be erroneously "fixed"
def test_valid_phrases():
    for phrase in phrases:
        yield check_phrase, phrase


def check_phrase(text):
    # Check each valid phrase above, making sure that it doesn't get changed
    eq_(fix_encoding(text), text)
    eq_(fix_encoding(text.encode('utf-8').decode('latin-1')), text)

    # make sure that the opening punctuation is not the only thing that makes
    # it work
    eq_(fix_encoding(text[1:]), text[1:])
    eq_(fix_encoding(text[1:].encode('utf-8').decode('latin-1')), text[1:])


def test_fix_with_backslash():
    eq_(fix_encoding("<40\\% vs \xe2\x89\xa540\\%"), "<40\\% vs ≥40\\%")


def test_mixed_utf8():
    eq_(fix_encoding('\xe2\x80\x9cmismatched quotes\x85\x94'), '“mismatched quotes…”')
    eq_(fix_encoding('â€œmismatched quotesâ€¦”'), '“mismatched quotes…”')


def test_lossy_utf8():
    eq_(fix_encoding('â€œlossy decodingâ€�'), '“lossy decoding�')


def test_unknown_emoji():
    # Make a string with two burritos in it. Python doesn't know about Unicode
    # burritos, but ftfy can guess they're probably emoji anyway.
    emoji_text = 'dos burritos: \U0001f32f\U0001f32f'

    # Mangle the burritos into a mess of Russian characters. (It would have
    # been great if we could have decoded them in cp437 instead, to turn them
    # into "DOS burritos", but the resulting string is one ftfy could already
    # fix.)
    emojibake = emoji_text.encode('utf-8').decode('windows-1251')

    # Restore the original text.
    eq_(fix_encoding(emojibake), emoji_text)

    # This doesn't happen if we replace the burritos with arbitrary unassigned
    # characters. The mangled text passes through as is.
    not_emoji = 'dos burritos: \U0003f32f\U0003f32f'.encode('utf-8').decode('windows-1251')
    eq_(fix_encoding(not_emoji), not_emoji)

    # The range we accept as emoji has gotten larger. Let's make sure we can
    # decode the futuristic emoji U+1F960, which will probably be a picture of
    # a fortune cookie in Unicode 10.0:
    emoji_text = "\U0001f960 I see emoji in your future"
    emojibake = emoji_text.encode('utf-8').decode('windows-1252')
    eq_(fix_encoding(emojibake), emoji_text)

    # We believe enough in the future of this codepoint that we'll even
    # recognize it with a mangled byte A0
    emojibake = emojibake.replace('\xa0', ' ')

    # Increment the first byte to get a very similar test case, but a
    # codepoint that will definitely not exist anytime soon. In this case,
    # we consider the existing text, "ñŸ¥\xa0", to be more probable.
    not_emoji = "\U0005f960 I see mojibake in your present".encode('utf-8').decode('windows-1252')
    eq_(fix_encoding(not_emoji), not_emoji)
