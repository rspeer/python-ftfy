import pytest

from ftfy.formatting import (
    character_width,
    display_center,
    display_ljust,
    display_rjust,
    monospaced_width,
)


class TestMonospacedWidth:
    def test_ascii_and_cjk(self):
        assert monospaced_width("hello") == 5
        assert monospaced_width("中文") == 4
        assert monospaced_width("ちゃぶ台返し") == 12
        assert monospaced_width("Hello 中文 👍") == 13

    def test_grapheme_clusters(self):
        assert monospaced_width("cafe\u0301") == 4
        assert monospaced_width("\u200d") == 0
        assert monospaced_width("👨‍👩‍👧") == 2
        assert monospaced_width("👩🏻‍💻") == 2
        assert monospaced_width("🇨🇦") == 2
        assert monospaced_width("❤️") == 2

    def test_ansi_escape_sequences(self):
        assert monospaced_width("\x1b[31mred\x1b[0m") == 3
        assert monospaced_width("\x1b[34mblue\x1b[m") == 4
        assert monospaced_width("\x1b[31;1mBold Red\x1b[0m") == 8

    def test_osc8_hyperlinks(self):
        assert monospaced_width("\x1b]8;;https://example.com\x07Click here\x1b]8;;\x07") == 10
        assert monospaced_width(
            "\x1b]8;;https://example.com\x07\x1b[34mBlue Link\x1b[0m\x1b]8;;\x07"
        ) == 9

    def test_control_characters(self):
        assert monospaced_width("example\x80") == 7
        assert monospaced_width("aaa\b\b\bxxx") == 3
        assert monospaced_width("hello\b\bXX") == 5


class TestCharacterWidth:
    def test_character_widths(self):
        assert character_width("A") == 1
        assert character_width("車") == 2
        assert character_width("\N{ZERO WIDTH JOINER}") == 0
        assert character_width("\n") == -1


class TestDisplayJustify:
    def test_ljust(self):
        assert display_ljust("hello", 10) == "hello     "
        assert display_ljust("中", 4) == "中  "
        assert display_ljust("👍", 4) == "👍  "
        assert display_ljust("hello", 3) == "hello"
        assert display_ljust("hi", 5, ".") == "hi..."

    def test_rjust(self):
        assert display_rjust("hello", 10) == "     hello"
        assert display_rjust("中", 4) == "  中"
        assert display_rjust("👍", 4) == "  👍"

    def test_center(self):
        assert display_center("hi", 6) == "  hi  "
        assert display_center("中", 6) == "  中  "
        assert display_center("hi", 5) == "  hi "

    def test_invalid_fillchar(self):
        with pytest.raises(ValueError, match="display width 1"):
            display_ljust("hi", 10, "中")
        with pytest.raises(ValueError, match="display width 1"):
            display_ljust("hi", 10, "\u200d")
        with pytest.raises(ValueError, match="display width 1"):
            display_rjust("hi", 10, "中")
        with pytest.raises(ValueError, match="display width 1"):
            display_center("hi", 10, "中")


