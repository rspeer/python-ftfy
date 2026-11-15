import pytest

from ftfy import TextFixerConfig, fix_and_explain, fix_text, fix_text_segment

ENCODING_OPTIONS = [
    ("restore_byte_a0", "voil\xc3  le travail", "voil\xe0  le travail"),
    ("replace_lossy_sequences", "\xc3\ufffdtude", "\xc3\ufffdtude"),
    ("decode_inconsistent_utf8", "\u2603 caf\xc3\xa9", "\u2603 caf\xc3\xa9"),
    ("fix_c1_controls", "\x94\u044f", "\x94\u044f"),
]


@pytest.mark.parametrize("option, text, expected", ENCODING_OPTIONS)
@pytest.mark.parametrize("fixer", [fix_text, fix_text_segment])
def test_encoding_options_without_explanations(fixer, option, text, expected):
    options = {option: False}
    assert fixer(text, **options) == expected
    assert fixer(text, TextFixerConfig(explain=False, **options)) == expected
    assert fixer(text, TextFixerConfig(explain=True, **options)) == expected


@pytest.mark.parametrize("option, text, expected", ENCODING_OPTIONS)
def test_explanation_setting_preserves_encoding_options(option, text, expected):
    options = {option: False}
    fixed, explanation = fix_and_explain(text, explain=False, **options)
    assert fixed == expected
    assert explanation is None

    fixed, explanation = fix_and_explain(text, explain=True, **options)
    assert fixed == expected
    assert explanation is not None
