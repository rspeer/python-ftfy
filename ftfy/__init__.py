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
             normalization='NFC',
             fix_latin_ligatures=True,
             uncurl_quotes=True,
             fix_line_breaks=True,
             fix_surrogates=True,
             remove_control_chars=True,
             remove_bom=True,
             max_decode_length=2**16):
    r"""
    Given Unicode text as input, make its representation consistent and
    possibly less broken.

    Let's start with some examples:

        >>> print(fix_text('uÌˆnicode'))
        ünicode

        >>> print(fix_text('Broken text&hellip; it&#x2019;s ﬂubberiﬁc!',
        ...                normalization='NFKC'))
        Broken text... it's flubberific!

        >>> print(fix_text('HTML entities &lt;3'))
        HTML entities <3

        >>> print(fix_text('<em>HTML entities &lt;3</em>'))
        <em>HTML entities &lt;3</em>

        >>> print(fix_text('\001\033[36;44mI&#x92;m blue, da ba dee da ba '
        ...               'doo&#133;\033[0m', normalization='NFKC'))
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

      - The default normalization, NFC, combines characters and diacritics that
        are written using separate code points, such as converting "e" plus an
        acute accent modifier into "é", or converting "ka" (か) plus a dakuten
        into the single character "ga" (が). Unicode can be converted to NFC
        form without any change in its meaning.
      
      - If you ask for NFKC normalization, it will apply additional
        normalizations that can change the meanings of characters. For example,
        ellipsis characters will be replaced with three periods, all ligatures
        will be replaced with the individual characters that make them up,
        and characters that differ in font style will be converted to the same
        character.

    - If `uncurl_quotes` is True, replace various curly quotation marks with
      plain-ASCII straight quotes.
    - If `fix_latin_ligatures` is True, then ligatures made of Latin letters,
      such as `ﬁ`, will be separated into individual letters. These ligatures are
      usually not meaningful outside of font rendering, and often represent
      copy-and-paste errors.
    - If `fix_line_breaks` is true, convert all line breaks to Unix style
      (CRLF and CR line breaks become LF line breaks).
    - If `fix_surrogates` is true, ensure that there are no UTF-16 surrogates
      in the resulting string, by converting them to the correct characters
      when they're appropriately paired, or replacing them with \ufffd
      otherwise.
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
                fix_latin_ligatures=fix_latin_ligatures,
                fix_line_breaks=fix_line_breaks,
                fix_surrogates=fix_surrogates,
                remove_control_chars=remove_control_chars,
                remove_bom=remove_bom
            )
        )
        pos = textbreak

    return ''.join(out)

ftfy = fix_text


def fix_encoding(text):
    return fixes.fix_encoding(text)


def fix_file(input_file,
             encoding=None,
             fix_entities='auto',
             remove_terminal_escapes=True,
             fix_encoding=True,
             normalization='NFC',
             fix_latin_ligatures=True,
             uncurl_quotes=True,
             fix_line_breaks=True,
             fix_surrogates=True,
             remove_control_chars=True,
             remove_bom=True):
    """
    Fix text that is found in a file.

    If the file is being read as Unicode text, use that. If it's being read as
    bytes, then unfortunately, we have to guess what encoding it is. We'll try
    a few common encodings, but we make no promises. See the `guess_bytes`
    function for how this is done.

    The output is a stream of fixed lines of text.
    """
    entities = fix_entities
    for line in input_file:
        if isinstance(line, bytes):
            if encoding is None:
                line, encoding = guess_bytes(line)
            else:
                line = line.decode(encoding)
        if fix_entities == 'auto' and '<' in line and '>' in line:
            entities = False
        yield fix_text_segment(
            line,
            fix_entities=entities,
            remove_terminal_escapes=remove_terminal_escapes,
            fix_encoding=fix_encoding,
            normalization=normalization,
            fix_latin_ligatures=fix_latin_ligatures,
            uncurl_quotes=uncurl_quotes,
            fix_line_breaks=fix_line_breaks,
            fix_surrogates=fix_surrogates,
            remove_control_chars=remove_control_chars,
            remove_bom=remove_bom
        )


def fix_text_segment(text,
                     fix_entities='auto',
                     remove_terminal_escapes=True,
                     fix_encoding=True,
                     normalization='NFC',
                     fix_latin_ligatures=True,
                     uncurl_quotes=True,
                     fix_line_breaks=True,
                     fix_surrogates=True,
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
        if fix_latin_ligatures:
            text = fixes.fix_latin_ligatures(text)
        if uncurl_quotes:
            text = fixes.uncurl_quotes(text)
        if fix_line_breaks:
            text = fixes.fix_line_breaks(text)
        if fix_surrogates:
            text = fixes.fix_surrogates(text)
        if remove_control_chars:
            text = fixes.remove_control_chars(text)
        if remove_bom:
            text = fixes.remove_bom(text)
        if text == origtext:
            return text


def guess_bytes(bstring):
    """
    NOTE: Using `guess_bytes` is not the recommended way of using ftfy. It's
    not the primary purpose of ftfy.

    In the unfortunate situation that you have some bytes in an unknown
    encoding, ftfy can guess a reasonable strategy for decoding them, by trying
    a few common encodings that can be distinguished from each other.

    Unlike the rest of ftfy, this may not be accurate, and it may *create*
    Unicode problems instead of solving them!
    
    It doesn't try East Asian encodings at all, and if you have East Asian text
    that you don't know how to decode, you are somewhat out of luck.  East
    Asian encodings require some serious statistics to distinguish from each
    other, so we can't support them without decreasing the accuracy of ftfy.
    
    If you don't know which encoding you have at all, I recommend
    trying the 'chardet' module, but being appropriately skeptical about its
    results.

    The encodings we try here are:

    - UTF-16 with a byte order mark, because a UTF-16 byte order mark looks
      like nothing else
    - UTF-8, because it's the global standard, which has been used by a
      majority of the Web since 2008
    - "utf-8-variants", because it's what people actually implement when they
      think they're doing UTF-8
    - MacRoman, because Microsoft Office thinks it's still a thing, and it
      can be distinguished by its line breaks. (If there are no line breaks in
      the string, though, you're out of luck.)
    - "sloppy-windows-1252", the Latin-1-like encoding that is the most common
      single-byte encoding
    """
    if bstring.startswith(b'\xfe\xff') or bstring.startswith(b'\xff\xfe'):
        return bstring.decode('utf-16'), 'utf-16'

    byteset = set(bytes(bstring))
    byte_ed, byte_c0, byte_CR, byte_LF = b'\xed\xc0\r\n'

    try:
        if byte_ed in byteset or byte_c0 in byteset:
            # Byte 0xed can be used to encode a range of codepoints that
            # are UTF-16 surrogates. UTF-8 does not use UTF-16 surrogates,
            # so when we see 0xed, it's very likely we're being asked to
            # decode CESU-8, the variant that encodes UTF-16 surrogates
            # instead of the original characters themselves.
            #
            # This will occasionally trigger on standard UTF-8, as there
            # are some Korean characters that also use byte 0xed, but that's
            # not harmful.
            #
            # Byte 0xc0 is impossible because, numerically, it would only
            # encode characters lower than U+0040. Those already have
            # single-byte representations, and UTF-8 requires using the
            # shortest possible representation. However, Java hides the null
            # codepoint, U+0000, in a non-standard longer representation -- it
            # encodes it as 0xc0 0x80 instead of 0x00, guaranteeing that 0x00
            # will never appear in the encoded bytes.
            #
            # The 'utf-8-variants' decoder can handle both of these cases, as
            # well as standard UTF-8, at the cost of a bit of speed.
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

    It breaks down a string, showing you for each codepoint its number in
    hexadecimal, its glyph, its category in the Unicode standard, and its name
    in the Unicode standard.

        >>> explain_unicode('(╯°□°)╯︵ ┻━┻')
        U+0028  (       [Ps] LEFT PARENTHESIS
        U+256F  ╯       [So] BOX DRAWINGS LIGHT ARC UP AND LEFT
        U+00B0  °       [So] DEGREE SIGN
        U+25A1  □       [So] WHITE SQUARE
        U+00B0  °       [So] DEGREE SIGN
        U+0029  )       [Pe] RIGHT PARENTHESIS
        U+256F  ╯       [So] BOX DRAWINGS LIGHT ARC UP AND LEFT
        U+FE35  ︵       [Ps] PRESENTATION FORM FOR VERTICAL LEFT PARENTHESIS
        U+0020          [Zs] SPACE
        U+253B  ┻       [So] BOX DRAWINGS HEAVY UP AND HORIZONTAL
        U+2501  ━       [So] BOX DRAWINGS HEAVY HORIZONTAL
        U+253B  ┻       [So] BOX DRAWINGS HEAVY UP AND HORIZONTAL
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
