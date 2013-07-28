# -*- coding: utf-8 -*-
"""
ftfy: fixes text for you

This is a module for making text less broken. See the `fix_text` function
for more information.
"""

from __future__ import unicode_literals
from ftfy import fixes
import unicodedata


MAXLEN = 65536

def fix_text(text, 
             fix_entities=True,
             remove_terminal_escapes=True,
             fix_encoding=True,
             normalization='NFKC',
             uncurl_quotes=True,
             remove_control_chars=True,
             remove_bom=True):
    """
    Given Unicode text as input, make its representation consistent and
    possibly less broken, by applying these steps in order:

    - If `remove_terminal_escapes` is True, remove sequences of bytes that are
      instructions for Unix terminals, such as the codes that make text appear
      in different colors.
    - If `fix_entities` is True, consider replacing HTML entities with their
      equivalent characters. However, this never applies to text with a pair
      of angle brackets in it already; you're probably not supposed to decode
      entities there, and you'd make things ambiguous if you did.
    - If `fix_encoding` is True, look for common mistakes that come from
      encoding or decoding Unicode text incorrectly, and fix them if they are
      reasonably fixable. See `fix_text_encoding` for details.
    - If `normalization` is not None, apply the specified form of Unicode
      normalization, which can be one of 'NFC', 'NFKC', 'NFD', and 'NFKD'.
      The default, 'NFKC', applies the following relevant transformations:
      - C: Combine characters and diacritics that are written using separate
        code points, such as converting "e" plus an acute accent modifier
        into "é", or converting "ka" (か) plus a dakuten into the
        single character "ga" (が).
      - K: Replace characters that are functionally equivalent with the most
        common form. For example, half-width katakana will be replaced with
        full-width versions, full-width Roman characters will be replaced with
        ASCII characters, ellipsis characters will be replaced with three
        periods, and the ligature 'ﬂ' will be replaced with 'fl'.
    - If `uncurl_quotes` is True, replace various curly quotation marks with
      plain-ASCII straight quotes.
    - If `remove_bom` is True, remove the Byte-Order Mark if it exists.
    - If anything was changed, repeat all the steps, so that the function is
      idempotent. "&amp;amp;" will become "&", for example, not "&amp;".

        >>> print(fix_text('uÌˆnicode'))
        ünicode

        >>> print(fix_text('Broken text&hellip; it&#x2019;s ﬂubberiﬁc!'))
        Broken text... it's flubberific!

        >>> print(fix_text('HTML entities &lt;3'))
        HTML entities <3

        >>> print(fix_text('<em>HTML entities &lt;3</em>'))
        <em>HTML entities &lt;3</em>

        >>> print(fix_text('\001\033[36;44mI&#x92;m blue, da ba dee da ba '
        ...               'doo&#133;\033[0m'))
        I'm blue, da ba dee da ba doo...

        >>> print(fix_text('\\ufeffParty like\\nit&rsquo;s 1999!'))
        Party like
        it's 1999!

        >>> len(fix_text('ﬁ' * 100000))
        200000

        >>> len(fix_text(''))
        0

    `fix_text` will work one line at a time, with the possibility that some
    lines are in different encodings.

    If you are certain your entire text is in the same encoding (though that
    encoding is possibly flawed), and do not mind performing operations on
    the whole text at once, use `fix_text_segment`.
    """
    out = []
    pos = 0
    while pos < len(text):
        textbreak = text.find('\n', pos, pos + MAXLEN)
        if textbreak == -1:
            if pos + MAXLEN >= len(text):
                textbreak = len(text) - 1
            else:
                textbreak = text.find(' ', pos, pos + MAXLEN)
                if textbreak == -1:
                    # oh well. We might not be able to fix the 2**16th character.
                    textbreak = MAXLEN

        substring = text[pos:pos + textbreak + 1]

        if '<' in substring and '>' in substring:
            # we see angle brackets together; this could be HTML
            fix_entities = False

        out.append(
            fix_text_segment(
                substring,
                fix_entities=fix_entities,
                remove_terminal_escapes=remove_terminal_escapes,
                fix_encoding=fix_encoding,
                normalization=normalization,
                uncurl_quotes=uncurl_quotes,
                remove_control_chars=remove_control_chars,
                remove_bom=remove_bom
            )
        )
        pos += textbreak + 1

    return ''.join(out)

ftfy = fix_text


def fix_file(file, normalization='NFKC'):
    """
    Fix a file that is being read in as Unicode text (for example, using
    the `codecs.open` function), and stream the resulting text one line
    at a time.
    """
    entities = True
    for line in file:
        if isinstance(line, bytes):
            raise UnicodeError("fix_file wants Unicode as input, so that "
                "it knows what to fix.\n"
                "Try this: codecs.open(file, encoding='utf-8')")
        if '<' in line and '>' in line:
            entities = False
        yield fix_text_segment(line, normalization, entities)


def fix_text_segment(text, 
                     fix_entities=True,
                     remove_terminal_escapes=True,
                     fix_encoding=True,
                     normalization='NFKC',
                     uncurl_quotes=True,
                     remove_control_chars=True,
                     remove_bom=True):
    """
    Apply fixes to text in a single chunk. This could be a line of text
    within a larger run of `fix_text`, or it could be a larger amount
    of text that you are certain is all in the same encoding.

    See `fix_text` for a description of the parameters.
    """
    if isinstance(text, bytes):
        raise UnicodeError(fixes.BYTES_ERROR_TEXT)

    unsafe_entities = ('<' in text and '>' in text)
    while True:
        origtext = text
        if fix_entities and not unsafe_entities:
            text = fixes.unescape_html(text)
        if remove_terminal_escapes:
            text = fixes.remove_terminal_escapes(text)
        if fix_encoding:
            text = fixes.fix_text_encoding(text)
        if normalization is not None:
            text = unicodedata.normalize(normalization, text)
        if uncurl_quotes:
            text = fixes.uncurl_quotes(text)
        if remove_control_chars:
            text = fixes.remove_control_chars(text)
        if remove_bom:
            text = fixes.remove_bom(text)

        if text == origtext:
            return text


fix_text_encoding = fixes.fix_text_encoding
