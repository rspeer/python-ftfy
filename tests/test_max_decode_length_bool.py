"""max_decode_length must reject bool (bool subclasses int → True becomes 1)."""

import pytest

from ftfy import TextFixerConfig, fix_text


def test_max_decode_length_rejects_bool():
    """bool subclasses int; max_decode_length=True must not silently become 1."""
    for value in (True, False):
        with pytest.raises(TypeError, match="max_decode_length must be an int, not bool"):
            fix_text("âœ” No problems", max_decode_length=value)
        with pytest.raises(TypeError, match="max_decode_length must be an int, not bool"):
            fix_text("âœ” No problems", TextFixerConfig(max_decode_length=value))
    # valid int still accepted; large enough to fix mojibake across the string
    assert fix_text("âœ” No problems", max_decode_length=1000) == "✔ No problems"
