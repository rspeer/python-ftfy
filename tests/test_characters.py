from ftfy.fixes import (
    fix_encoding, fix_encoding_and_explain, apply_plan, possible_encoding,
    remove_control_chars, fix_surrogates
)
from ftfy.badness import badness
import unicodedata
import sys
from ftfy.char_classes import CHAR_CLASS_STRING


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, 'latin-1')


def test_byte_order_mark():
    assert fix_encoding('ï»¿') == '\ufeff'


def test_control_chars():
    text = (
        "\ufeffSometimes, \ufffcbad ideas \x7f\ufffalike these characters\ufffb "
        "\u206aget standardized\U000E0065\U000E006E.\r\n"
    )
    fixed = "Sometimes, bad ideas like these characters get standardized.\r\n"
    assert remove_control_chars(text) == fixed


def test_emoji_variation_selector():
    # The hearts here are explicitly marked as emoji using the variation
    # selector U+FE0F. This is not weird.
    assert badness('❤\ufe0f' * 10) == 0


def test_emoji_skintone_selector():
    # Dear heuristic, you can't call skin-tone selectors weird anymore.
    # We welcome Santa Clauses of all colors.
    assert badness('🎅🏿🎅🏽🎅🏼🎅🏻') == 0


def test_surrogates():
    assert fix_surrogates('\udbff\udfff') == '\U0010ffff'
    assert fix_surrogates('\ud800\udc00') == '\U00010000'


def test_char_class_type():
    assert isinstance(CHAR_CLASS_STRING, str)
