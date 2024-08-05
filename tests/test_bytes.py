import pytest

from ftfy import guess_bytes
from ftfy.bad_codecs.utf8_variants import IncrementalDecoder

TEST_ENCODINGS = ["utf-16", "utf-8", "sloppy-windows-1252"]

TEST_STRINGS = [
    "Renée\nFleming",
    "Noël\nCoward",
    "Señor\nCardgage",
    "€ • £ • ¥",
    "¿Qué?",
]


@pytest.mark.parametrize("string", TEST_STRINGS)
def test_guess_bytes(string):
    for encoding in TEST_ENCODINGS:
        result_str, result_encoding = guess_bytes(string.encode(encoding))
        assert result_str == string
        assert result_encoding == encoding

    if "\n" in string:
        old_mac_bytes = string.replace("\n", "\r").encode("macroman")
        result_str, result_encoding = guess_bytes(old_mac_bytes)
        assert result_str == string.replace("\n", "\r")


def test_guess_bytes_null():
    bowdlerized_null = b"null\xc0\x80separated"
    result_str, result_encoding = guess_bytes(bowdlerized_null)
    assert result_str == "null\x00separated"
    assert result_encoding == "utf-8-variants"


def test_incomplete_sequences():
    test_bytes = b"surrogates: \xed\xa0\x80\xed\xb0\x80 / null: \xc0\x80"
    test_string = "surrogates: \U00010000 / null: \x00"

    # Test that we can feed this string to decode() in multiple pieces, and no
    # matter where the break between those pieces is, we get the same result.
    for split_point in range(len(test_string) + 1):
        left = test_bytes[:split_point]
        right = test_bytes[split_point:]

        decoder = IncrementalDecoder()
        got = decoder.decode(left, final=False)
        got += decoder.decode(right)
        assert got == test_string
