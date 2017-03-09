from ftfy.fixes import (
    fix_encoding, fix_encoding_and_explain, apply_plan, possible_encoding,
    remove_control_chars, fix_surrogates
)
from ftfy.badness import sequence_weirdness
import unicodedata
import sys
from nose.tools import eq_


# Most single-character strings which have been misencoded should be restored.
def test_bmp_characters():
    for index in range(0xa0, 0xfffd):
        char = chr(index)
        # Exclude code points that are not assigned
        if unicodedata.category(char) not in ('Co', 'Cn', 'Cs', 'Mc', 'Mn', 'Sk'):
            garble = char.encode('utf-8').decode('latin-1')
            # Exclude characters whose re-encoding is protected by the
            # 'sequence_weirdness' metric
            if sequence_weirdness(garble) >= 0:
                garble2 = char.encode('utf-8').decode('latin-1').encode('utf-8').decode('latin-1')
                for garb in (garble, garble2):
                    fixed, plan = fix_encoding_and_explain(garb)
                    eq_(fixed, char)
                    eq_(apply_plan(garb, plan), char)


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, 'latin-1')


def test_byte_order_mark():
    eq_(fix_encoding('ï»¿'), '\ufeff')


def test_control_chars():
    text = (
        "\ufeffSometimes, \ufffcbad ideas \x7f\ufffalike these characters\ufffb "
        "\u206aget standardized\U000E0065\U000E006E.\r\n"
    )
    fixed = "Sometimes, bad ideas like these characters get standardized.\r\n"
    eq_(remove_control_chars(text), fixed)


def test_emoji_variation_selector():
    # The hearts here are explicitly marked as emoji using the variation
    # selector U+FE0F. This is not weird.
    eq_(sequence_weirdness('❤\ufe0f' * 10), 0)


def test_emoji_skintone_selector():
    # Dear heuristic, you can't call skin-tone selectors weird anymore.
    # We welcome Santa Clauses of all colors.
    eq_(sequence_weirdness('🎅🏿🎅🏽🎅🏼🎅🏻'), 0)


def test_surrogates():
    eq_(fix_surrogates('\udbff\udfff'), '\U0010ffff')
    eq_(fix_surrogates('\ud800\udc00'), '\U00010000')

