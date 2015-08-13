# coding: utf-8
from __future__ import unicode_literals, division
from unicodedata import east_asian_width, combining, category, normalize


def character_width(char):
    """
    Determine the width that a character is likely to be displayed as in
    a monospaced terminal. The width will always be 0, 1, or 2.

    We are assuming that the character will appear in a modern, Unicode-aware
    terminal emulator, where CJK characters -- plus characters designated
    "fullwidth" by CJK encodings -- will span two character cells. (Maybe
    it's an over-simplification to call these displays "monospaced".)

    When a character width is "Ambiguous", we assume it to span one character
    cell, because we assume that the monospaced display you're using is
    designed mostly to display Western characters with CJK characters as the
    exception. This assumption will go wrong, for example, if your display is
    actually on a Japanese flip-phone... but let's assume it isn't.

    Combining marks and formatting codepoints do not advance the cursor,
    so their width is 0.

    If the character is a particular kind of control code -- the kind
    represented by the lowest bytes of ASCII, with Unicode category Cc -- the
    idea of it having a "width" probably doesn't even apply, because it will
    probably have some other effect on your terminal. For example, there's no
    sensible width for a line break. We return the default of 1 in the absence
    of anything sensible to do there.

    >>> character_width('車')
    2
    >>> character_width('A')
    1
    >>> character_width('\N{SOFT HYPHEN}')
    0
    """
    if combining(char) != 0:
        # Combining characters don't advance the cursor; they modify the
        # previous character instead.
        return 0
    elif east_asian_width(char) in 'FW':
        # Characters designated Wide (W) or Fullwidth (F) will take up two
        # columns in many Unicode-aware terminal emulators.
        return 2
    elif category(char) == 'Cf':
        # Characters in category Cf are un-printable formatting characters
        # that do not advance the cursor, such as zero-width spaces or
        # right-to-left marks.
        return 0
    else:
        return 1


def monospaced_width(text):
    """
    Return the number of character cells that this string is likely to occupy
    when displayed in a monospaced, modern, Unicode-aware terminal emulator.
    We refer to this as the "display width" of the string.

    This can be useful for formatting text that may contain non-spacing
    characters, or CJK characters that take up two character cells.

    >>> monospaced_width('ちゃぶ台返し')
    12
    >>> len('ちゃぶ台返し')
    6
    """
    # NFC-normalize the text first, so that we don't need special cases for
    # Hangul jamo.
    text = normalize('NFC', text)
    return sum([character_width(char) for char in text])


def display_ljust(text, width, fillchar=' '):
    """
    Return `text` left-justified in a Unicode string whose display width,
    in a monospaced terminal, should be at least `width` character cells.
    The rest of the string will be padded with `fillchar`, which must be
    a width-1 character.

    "Left" here means toward the beginning of the string, which may actually
    appear on the right in an RTL context. This is similar to the use of the
    word "left" in "left parenthesis".

    >>> lines = ['Table flip', '(╯°□°)╯︵ ┻━┻', 'ちゃぶ台返し']
    >>> for line in lines:
    ...     print(display_ljust(line, 20, '▒'))
    Table flip▒▒▒▒▒▒▒▒▒▒
    (╯°□°)╯︵ ┻━┻▒▒▒▒▒▒▒
    ちゃぶ台返し▒▒▒▒▒▒▒▒
    """
    if character_width(fillchar) != 1:
        raise ValueError("The padding character must have display width 1")
    padding = max(0, width - monospaced_width(text))
    return text + fillchar * padding


def display_rjust(text, width, fillchar=' '):
    """
    Return `text` right-justified in a Unicode string whose display width,
    in a monospaced terminal, should be at least `width` character cells.
    The rest of the string will be padded with `fillchar`, which must be
    a width-1 character.

    "Right" here means toward the end of the string, which may actually be on
    the left in an RTL context. This is similar to the use of the word "right"
    in "right parenthesis".

    >>> lines = ['Table flip', '(╯°□°)╯︵ ┻━┻', 'ちゃぶ台返し']
    >>> for line in lines:
    ...     print(display_rjust(line, 20, '▒'))
    ▒▒▒▒▒▒▒▒▒▒Table flip
    ▒▒▒▒▒▒▒(╯°□°)╯︵ ┻━┻
    ▒▒▒▒▒▒▒▒ちゃぶ台返し
    """
    if character_width(fillchar) != 1:
        raise ValueError("The padding character must have display width 1")
    padding = max(0, width - monospaced_width(text))
    return fillchar * padding + text


def display_center(text, width, fillchar=' '):
    """
    Return `text` centered in a Unicode string whose display width, in a
    monospaced terminal, should be at least `width` character cells. The rest
    of the string will be padded with `fillchar`, which must be a width-1
    character.

    >>> lines = ['Table flip', '(╯°□°)╯︵ ┻━┻', 'ちゃぶ台返し']
    >>> for line in lines:
    ...     print(display_center(line, 20, '▒'))
    ▒▒▒▒▒Table flip▒▒▒▒▒
    ▒▒▒(╯°□°)╯︵ ┻━┻▒▒▒▒
    ▒▒▒▒ちゃぶ台返し▒▒▒▒
    """
    if character_width(fillchar) != 1:
        raise ValueError("The padding character must have display width 1")
    padding = max(0, width - monospaced_width(text))
    left_padding = padding // 2
    right_padding = padding - left_padding
    return fillchar * left_padding + text + fillchar * right_padding

