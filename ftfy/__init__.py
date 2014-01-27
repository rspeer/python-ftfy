# -*- coding: utf-8 -*-
"""
ftfy: fixes text for you

This is a module for making text less broken. See the `fix_text` function
for more information.
"""

from __future__ import unicode_literals

# See the docstring for ftfy.bad_codecs to see what we're doing here.
import ftfy.bad_codecs
ftfy.bad_codecs.ok()

from ftfy import fixes
from ftfy.fixes import fix_text_encoding
from ftfy.compatibility import is_printable
import unicodedata
import warnings


def fix_text(text,
             fix_entities='auto',
             remove_terminal_escapes=True,
             fix_encoding=True,
             normalization='NFKC',
             uncurl_quotes=True,
             fix_line_breaks=True,
             remove_control_chars=True,
             remove_bom=True,
             max_decode_length=2**16):
    r"""
    Given Unicode text as input, make its representation consistent and
    possibly less broken.

    Let's start with some examples:

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

        >>> # This example string starts with a byte-order mark, even if
        >>> # you can't see it on the Web.
        >>> print(fix_text('\ufeffParty like\nit&rsquo;s 1999!'))
        Party like
        it's 1999!

        >>> len(fix_text('ﬁ' * 100000))
        200000

        >>> len(fix_text(''))
        0

    Based on the options you provide, ftfy applies these steps in order:

    - If `fix_entities` is True, replace HTML entities with their equivalent
      characters. If it's "auto" (the default), then consider replacing HTML
      entities, but don't do so in text where you have seen a pair of actual
      angle brackets (that's probably actually HTML and you shouldn't mess
      with the entities).
    - If `remove_terminal_escapes` is True, remove sequences of bytes that are
      instructions for Unix terminals, such as the codes that make text appear
      in different colors.
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
    - If `fix_line_breaks` is true, convert all line breaks to Unix style
      (CRLF and CR line breaks become LF line breaks).
    - If `fix_control_characters` is true, remove all C0 control characters
      except the common useful ones: TAB, CR, LF, and FF. (CR characters
      may have already been removed by the `fix_line_breaks` step.)
    - If `remove_bom` is True, remove the Byte-Order Mark if it exists.
    - If anything was changed, repeat all the steps, so that the function is
      idempotent. "&amp;amp;" will become "&", for example, not "&amp;".

    `fix_text` will work one line at a time, with the possibility that some
    lines are in different encodings. When it encounters lines longer than
    `max_decode_length`, it will not run the `fix_encoding` step, to avoid
    unbounded slowdowns.

    If you are certain your entire text is in the same encoding (though that
    encoding is possibly flawed), and do not mind performing operations on
    the whole text at once, use `fix_text_segment`.

    _`bug 18183`: http://bugs.python.org/issue18183
    """
    if isinstance(text, bytes):
        raise UnicodeError(fixes.BYTES_ERROR_TEXT)

    out = []
    pos = 0
    while pos < len(text):
        textbreak = text.find('\n', pos) + 1
        fix_encoding_this_time = fix_encoding
        if textbreak == 0:
            textbreak = len(text)
        if (textbreak - pos) > max_decode_length:
            fix_encoding_this_time = False

        substring = text[pos:textbreak]

        if fix_entities == 'auto' and '<' in substring and '>' in substring:
            # we see angle brackets together; this could be HTML
            fix_entities = False

        out.append(
            fix_text_segment(
                substring,
                fix_entities=fix_entities,
                remove_terminal_escapes=remove_terminal_escapes,
                fix_encoding=fix_encoding_this_time,
                normalization=normalization,
                uncurl_quotes=uncurl_quotes,
                fix_line_breaks=fix_line_breaks,
                remove_control_chars=remove_control_chars,
                remove_bom=remove_bom
            )
        )
        pos = textbreak

    return ''.join(out)

ftfy = fix_text


def fix_file(input_file,
             fix_entities='auto',
             remove_terminal_escapes=True,
             fix_encoding=True,
             normalization='NFKC',
             uncurl_quotes=True,
             fix_line_breaks=True,
             remove_control_chars=True,
             remove_bom=True):
    """
    Fix text that is found in a file.

    If the file is being read as Unicode text, use that. If it's being read as
    bytes, then unfortunately, we have to guess what encoding it is. We'll try
    a few common encodings, but we make no promises. See `guess_bytes.py` for
    how this is done.

    The output is a stream of fixed lines of text.
    """
    entities = fix_entities
    for line in input_file:
        if isinstance(line, bytes):
            line, encoding = guess_bytes(line)
        if fix_entities == 'auto' and '<' in line and '>' in line:
            entities = False
        yield fix_text_segment(
            line,
            fix_entities=fix_entities,
            remove_terminal_escapes=remove_terminal_escapes,
            fix_encoding=entities,
            normalization=normalization,
            uncurl_quotes=uncurl_quotes,
            fix_line_breaks=fix_line_breaks,
            remove_control_chars=remove_control_chars,
            remove_bom=remove_bom
        )


def fix_text_segment(text,
                     fix_entities='auto',
                     remove_terminal_escapes=True,
                     fix_encoding=True,
                     normalization='NFKC',
                     uncurl_quotes=True,
                     fix_line_breaks=True,
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

    if fix_entities == 'auto' and '<' in text and '>' in text:
        fix_entities = False
    while True:
        origtext = text
        if fix_entities:
            text = fixes.unescape_html(text)
        if remove_terminal_escapes:
            text = fixes.remove_terminal_escapes(text)
        if fix_encoding:
            text = fixes.fix_text_encoding(text)
        if normalization is not None:
            text = unicodedata.normalize(normalization, text)
        if uncurl_quotes:
            text = fixes.uncurl_quotes(text)
        if fix_line_breaks:
            text = fixes.fix_line_breaks(text)
        if remove_control_chars:
            text = fixes.remove_control_chars(text)
        if remove_bom:
            text = fixes.remove_bom(text)
        if text == origtext:
            return text


def guess_bytes(bstring):
    """
    If you have some bytes in an unknown encoding, here's a reasonable
    strategy for decoding them, by trying a few common encodings that
    can be distinguished from each other.

    This is not a magic bullet. If the bytes are coming from some MySQL
    database with the "character set" set to ISO Elbonian, this won't figure
    it out.

    The encodings we try are:

    - UTF-16 with a byte order mark, because a UTF-16 byte order mark looks
      like nothing else
    - UTF-8, because it's the global de facto standard
    - "utf-8-variants", because it's what people actually implement when they
      think they're doing UTF-8
    - MacRoman, because Microsoft Office thinks it's still a thing, and it
      can be distinguished by its line breaks. (If there are no line breaks in
      the string, though, you're out of luck.)
    - "sloppy-windows-1252", the Latin-1-like encoding that is the most common
      single-byte encoding
    """
    # Look for a byte-order mark to recognize UTF-16
    if bstring.startswith(b'\xfe\xff') or bstring.startswith(b'\xff\xfe'):
        return bstring.decode('utf-16'), 'utf-16'

    # Make a set out of the bytes, so we can quickly test for the presence of
    # certain bytes
    byteset = set(bytes(bstring))
    byte_ed, byte_c0, byte_CR, byte_LF = b'\xed\xc0\r\n'

    try:
        if byte_ed in byteset or byte_c0 in byteset:
            # Byte 0xed can only be used to encode a range of codepoints that
            # are UTF-16 surrogates. UTF-8 does not use UTF-16 surrogates, so
            # this byte is impossible in real UTF-8. Therefore, if we see
            # bytes that look like UTF-8 but contain 0xed, what we're seeing
            # is CESU-8, the variant that encodes UTF-16 surrogates instead
            # of the original characters themselves.
            #
            # Byte 0xc0 is impossible because, numerically, it would only
            # encode characters lower than U+40. Those already have single-byte
            # representations, and UTF-8 requires using the shortest possible
            # representation. However, Java hides the null codepoint, U+0, in a
            # non-standard longer representation -- it encodes it as 0xc0 0x80
            # instead of 0x00, guaranteeing that 0x00 will never appear in the
            # encoded bytes.
            #
            # The 'utf-8-variants' decoder can handle both of these cases.
            return bstring.decode('utf-8-variants'), 'utf-8-variants'
        else:
            return bstring.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        pass

    if byte_CR in bstring and byte_LF not in bstring:
        return bstring.decode('macroman'), 'macroman'
    else:
        return bstring.decode('sloppy-windows-1252'), 'sloppy-windows-1252'


def explain_unicode(text):
    """
    A utility method that's useful for debugging mysterious Unicode.
    """
    for char in text:
        if is_printable(char):
            display = char
        else:
            display = char.encode('unicode-escape').decode('ascii')
        print('U+{code:04X}  {display:<7} [{category}] {name}'.format(
            display=display,
            code=ord(char),
            category=unicodedata.category(char),
            name=unicodedata.name(char, '<unknown>')
        ))


def fix_bad_encoding(text):
    """
    Kept for compatibility with previous versions of ftfy.
    """
    warnings.warn(
        'fix_bad_encoding is now known as fix_text_encoding',
        DeprecationWarning
    )
    return fix_text_encoding(text)
