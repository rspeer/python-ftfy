from ftfy import (
    fix_and_explain,
    fix_encoding,
    fix_text,
)
from ftfy.chardata import possible_encoding
from ftfy.fixes import fix_surrogates, remove_control_chars


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, "latin-1")


def test_byte_order_mark():
    assert fix_encoding("ï»¿") == "\ufeff"


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


def test_ohio_flag():
    # I did not expect to find the "Flag of Ohio" emoji in the wild but there it is.
    # Test that this emoji (which no emoji database believes has been implemented)
    # passes through unchanged.
    text = "#superman #ohio 🏴\U000e0075\U000e0073\U000e006f\U000e0068\U000e007f #cleveland #usa 🇺🇸"
    assert fix_text(text) == text


def test_surrogates():
    assert fix_surrogates("\udbff\udfff") == "\U0010ffff"
    assert fix_surrogates("\ud800\udc00") == "\U00010000"


def test_color_escapes():
    fixed, plan = fix_and_explain("\001\033[36;44mfoo")
    print(plan)
    assert fixed == "foo"
    assert plan == [
        ("apply", "remove_terminal_escapes"),
        ("apply", "remove_control_chars"),
    ]
