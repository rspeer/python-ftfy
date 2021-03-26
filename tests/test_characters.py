from ftfy import fix_encoding, fix_encoding_and_explain, apply_plan
from ftfy.fixes import remove_control_chars, fix_surrogates
from ftfy.chardata import possible_encoding
from ftfy.badness import badness
import unicodedata
import sys


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, 'latin-1')


def test_byte_order_mark():
    assert fix_encoding('ï»¿') == '\ufeff'


def test_control_chars():
    text = (
        "\ufeffSometimes, \ufffcbad ideas \x7f\ufffalike these characters\ufffb "
        "\u206aget standardized.\r\n"
    )
    fixed = "Sometimes, bad ideas like these characters get standardized.\r\n"
    assert remove_control_chars(text) == fixed


def test_welsh_flag():
    # ftfy used to remove "tag characters", but they have been repurposed in the
    # "Flag of England", "Flag of Scotland", and "Flag of Wales" emoji sequences.
    text = "This flag has a dragon on it 🏴󠁧󠁢󠁷󠁬󠁳󠁿"
    assert remove_control_chars(text) == text


def test_surrogates():
    assert fix_surrogates('\udbff\udfff') == '\U0010ffff'
    assert fix_surrogates('\ud800\udc00') == '\U00010000'

