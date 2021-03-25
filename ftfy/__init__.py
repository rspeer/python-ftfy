"""
ftfy: fixes text for you

This is a module for making text less broken. See the `fix_text` function
for more information.
"""

import unicodedata
import warnings
from collections import namedtuple
from typing import Optional

import ftfy.bad_codecs
from ftfy import chardata, fixes
from ftfy.badness import is_bad
from ftfy.formatting import display_ljust

__version__ = "6.0"


# Though this function does nothing, it lets linters know that we're using
# ftfy.bad_codecs. See the docstring in `bad_codecs/__init__.py` for more.
ftfy.bad_codecs.ok()


CONFIG_DEFAULTS = {
    # Replace HTML entities, but not in strings where a < character
    # has appeared literally. Those strings are assumed to be HTML,
    # so entities should be left alone.
    "unescape_html": "auto",
    # Remove "ANSI" terminal escapes, such as for changing the color
    # of text in a terminal.
    "remove_terminal_escapes": True,
    # Detect mojibake, and attempt to decode the entire string in a
    # different encoding when it's detected.
    "fix_encoding": True,
    # When fixing mojibake, allow a literal space to be interpreted
    # as a non-breaking space, which would have been byte A0 in many
    # encodings.
    "restore_byte_a0": True,
    # Detect mojibake that has been partially replaced by the characters
    # '�' or '?', and replace the detected sequences with '�'.
    "replace_lossy_sequences": True,
    # Detect certain kinds of mojibake even when it's not consistent
    # across the entire string. Replace sufficiently clear sequences
    # of UTF-8 mojibake with the characters they should have been.
    "decode_inconsistent_utf8": True,
    # Replace C1 control characters with their Windows-1252 equivalents,
    # like HTML5 does.
    "fix_c1_controls": True,
    # Replace common Latin-alphabet ligatures, such as 'ﬁ', with the
    # letters they're made of.
    "fix_latin_ligatures": True,
    # Replace fullwidth Latin characters and halfwidth Katakana with
    # their more standard widths.
    "fix_character_width": True,
    # Replace curly quotes with straight quotes.
    "uncurl_quotes": True,
    # Replace various forms of line breaks with the standard Unix line
    # break, '\n'.
    "fix_line_breaks": True,
    # Replace sequences of UTF-16 surrogates with the character they were
    # meant to encode.
    "fix_surrogates": True,
    # Remove control characters that have no displayed effect on text.
    "remove_control_chars": True,
    # Change 'normalization' to 'NFKC' to apply Unicode compatibility
    # conversions. In some cases, this will change the meaning of text.
    #
    # You can also set it to None to apply no normalization, including
    # leaving all combining characters separate.
    "normalization": "NFC",
    # The maximum length of line that should be fixed by ftfy without
    # breaking it up into smaller strings.
    "max_decode_length": 1000000,
    # Set 'explain' to False to not compute explanations, possibly saving
    # time. The functions that return explanations will return None.
    "explain": True,
}
TextFixerConfig = namedtuple(
    "TextFixerConfig", CONFIG_DEFAULTS.keys(), defaults=CONFIG_DEFAULTS.values()
)


FIXERS = {
    "unescape_html": fixes.unescape_html,
    "remove_terminal_escapes": fixes.remove_terminal_escapes,
    "restore_byte_a0": fixes.restore_byte_a0,
    "replace_lossy_sequences": fixes.replace_lossy_sequences,
    "decode_inconsistent_utf8": fixes.decode_inconsistent_utf8,
    "fix_c1_controls": fixes.fix_c1_controls,
    "fix_latin_ligatures": fixes.fix_latin_ligatures,
    "fix_character_width": fixes.fix_character_width,
    "uncurl_quotes": fixes.uncurl_quotes,
    "fix_line_breaks": fixes.fix_line_breaks,
    "fix_surrogates": fixes.fix_surrogates,
    "remove_control_chars": fixes.remove_control_chars,
}


BYTES_ERROR_TEXT = """Hey wait, this isn't Unicode.

ftfy is designed to fix problems that were introduced by handling Unicode
incorrectly. It might be able to fix the bytes you just handed it, but the
fact that you just gave a pile of bytes to a function that fixes text means
that your code is *also* handling Unicode incorrectly.

ftfy takes Unicode text as input. You should take these bytes and decode
them from the encoding you think they are in. If you're not sure what encoding
they're in:

- First, try to find out. 'utf-8' is a good assumption.
- If the encoding is simply unknowable, try running your bytes through
  ftfy.guess_bytes. As the name implies, this may not always be accurate.

If you're confused by this, please read the Python Unicode HOWTO:

    http://docs.python.org/3/howto/unicode.html
"""


def _try_fix(fixer_name: str, text: str, steps: list) -> str:
    fixer = FIXERS[fixer_name]
    fixed = fixer(text)
    if fixed != text:
        steps.append(("apply", fixer_name))
    return fixed


def fix_text(text: str, config: Optional[TextFixerConfig] = None, **kwargs) -> str:
    r"""
    Given Unicode text as input, fix inconsistencies and glitches in it,
    such as mojibake.

    FIXME: clean up this docstring

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

        >>> print(fix_text("&macr;\\_(ã\x83\x84)_/&macr;"))
        ¯\_(ツ)_/¯

        >>> # This example string starts with a byte-order mark, even if
        >>> # you can't see it on the Web.
        >>> print(fix_text('\ufeffParty like\nit&rsquo;s 1999!'))
        Party like
        it's 1999!

        >>> print(fix_text('ＬＯＵＤ　ＮＯＩＳＥＳ'))
        LOUD NOISES

        >>> len(fix_text('ﬁ' * 100000))
        200000

        >>> len(fix_text(''))
        0

    Based on the options you provide, ftfy applies these steps in order:

    - If `remove_terminal_escapes` is True, remove sequences of bytes that are
      instructions for Unix terminals, such as the codes that make text appear
      in different colors.

    - If `fix_encoding` is True, look for common mistakes that come from
      encoding or decoding Unicode text incorrectly, and fix them if they are
      reasonably fixable. See `fixes.fix_encoding` for details.

    - If `fix_entities` is True, replace HTML entities with their equivalent
      characters. If it's "auto" (the default), then consider replacing HTML
      entities, but don't do so in text where you have seen a pair of actual
      angle brackets (that's probably actually HTML and you shouldn't mess
      with the entities).

    - If `uncurl_quotes` is True, replace various curly quotation marks with
      plain-ASCII straight quotes.

    - If `fix_latin_ligatures` is True, then ligatures made of Latin letters,
      such as `ﬁ`, will be separated into individual letters. These ligatures
      are usually not meaningful outside of font rendering, and often represent
      copy-and-paste errors.

    - If `fix_character_width` is True, half-width and full-width characters
      will be replaced by their standard-width form.

    - If `fix_line_breaks` is true, convert all line breaks to Unix style
      (CRLF and CR line breaks become LF line breaks).

    - If `fix_surrogates` is true, ensure that there are no UTF-16 surrogates
      in the resulting string, by converting them to the correct characters
      when they're appropriately paired, or replacing them with \ufffd
      otherwise.

    - If `remove_control_chars` is true, remove control characters that
      are not suitable for use in text. This includes most of the ASCII control
      characters, plus some Unicode controls such as the byte order mark
      (U+FEFF). Useful control characters, such as Tab, Line Feed, and
      bidirectional marks, are left as they are.

    - If `remove_bom` is True, remove the Byte-Order Mark at the start of the
      string if it exists. (This is largely redundant, because it's a special
      case of `remove_control_characters`. This option will become deprecated
      in a later version.)

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

    - If anything was changed, repeat all the steps, so that the function is
      idempotent. "&amp;amp;" will become "&", for example, not "&amp;".

    `fix_text` will work one line at a time, with the possibility that some
    lines are in different encodings, allowing it to fix text that has been
    concatenated together from different sources.

    When it encounters lines longer than `max_decode_length` (1 million
    codepoints by default), it will not run the `fix_encoding` step, to avoid
    unbounded slowdowns.

    If you're certain that any decoding errors in the text would have affected
    the entire text in the same way, and you don't mind operations that scale
    with the length of the text, you can use `fix_text_segment` directly to
    fix the whole string in one batch.

    ftfy can also provide an 'explanation', a list of transformations it applied
    to the text that would fix more text like it.

    However, this function doesn't provide explanations, because it can apply
    different fixes to different lines of text, and one explanation may not
    suffice.

    To get an explanation, use the :func:`fix_and_explain()` function.
    """

    if config is None:
        config = TextFixerConfig()
    config = config._replace(**kwargs)
    if isinstance(text, bytes):
        raise UnicodeError(fixes.BYTES_ERROR_TEXT)

    out = []
    pos = 0
    while pos < len(text):
        textbreak = text.find("\n", pos) + 1
        if textbreak == 0:
            textbreak = len(text)
        if (textbreak - pos) > config.max_decode_length:
            textbreak = pos + config.max_decode_length

        segment = text[pos:textbreak]
        if config.unescape_html == "auto" and "<" in segment:
            config = config._replace(unescape_html=False)
        fixed_segment, _ = fix_and_explain(segment, config)
        out.append(fixed_segment)
        pos = textbreak
    return "".join(out)


def fix_and_explain(text: str, config: Optional[TextFixerConfig] = None) -> (str, list):
    """
    Apply fixes to text in a single chunk, and also produce an explanation
    of what was fixed.

    Returns the fixed text, and a list explaining what was fixed.
    """
    if config is None:
        config = TextFixerConfig()
    if isinstance(text, bytes):
        raise UnicodeError(fixes.BYTES_ERROR_TEXT)

    fix_entities = config.unescape_html
    if fix_entities == "auto" and "<" in text:
        fix_entities = False

    steps = []
    while True:
        origtext = text

        if fix_entities:
            text = _try_fix("unescape_html", text, steps)

        if config.fix_encoding:
            text, encoding_steps = fix_encoding_and_explain(text, config)
            steps.extend(encoding_steps)

        for fixer in [
            "fix_c1_controls",
            "fix_latin_ligatures",
            "fix_character_width",
            "uncurl_quotes",
            "fix_line_breaks",
            "fix_surrogates",
            "remove_control_chars",
        ]:
            if getattr(config, fixer):
                text = _try_fix(fixer, text, steps)
        # TODO: backward compatibility for remove_bom

        if config.normalization is not None:
            fixed = unicodedata.normalize(config.normalization, text)
            if fixed != text:
                text = fixed
                steps.append(("normalize", config.normalization))

        if text == origtext:
            return text, steps


def fix_encoding_and_explain(text, config=None):
    if config is None:
        config = TextFixerConfig()
    if isinstance(text, bytes):
        raise UnicodeError(fixes.BYTES_ERROR_TEXT)
    if not config.fix_encoding:
        raise ValueError(
            "It doesn't make sense to run fix_encoding_and_explain "
            "with fix_encoding=False"
        )

    plan_so_far = []
    while True:
        prevtext = text
        text, plan = _fix_encoding_one_step_and_explain(text, config)
        plan_so_far.extend(plan)
        if text == prevtext:
            return text, plan_so_far


def _fix_encoding_one_step_and_explain(text, config):
    if config is None:
        config = TextFixerConfig()

    if len(text) == 0:
        return text, []

    # The first plan is to return ASCII text unchanged, as well as text
    # that doesn't look like it contains mojibake
    if chardata.possible_encoding(text, "ascii") or not is_bad(text):
        return text, []

    # As we go through the next step, remember the possible encodings
    # that we encounter but don't successfully fix yet. We may need them
    # later.
    possible_1byte_encodings = []

    # Suppose the text was supposed to be UTF-8, but it was decoded using
    # a single-byte encoding instead. When these cases can be fixed, they
    # are usually the correct thing to do, so try them next.
    for encoding in chardata.CHARMAP_ENCODINGS:
        if chardata.possible_encoding(text, encoding):
            possible_1byte_encodings.append(encoding)
            encoded_bytes = text.encode(encoding)
            encode_step = ("encode", encoding)
            transcode_steps = []

            # Now, find out if it's UTF-8 (or close enough). Otherwise,
            # remember the encoding for later.
            try:
                decoding = "utf-8"
                # Check encoded_bytes for sequences that would be UTF-8,
                # except they have b' ' where b'\xa0' would belong.
                if config.restore_byte_a0 and chardata.ALTERED_UTF8_RE.search(
                    encoded_bytes
                ):
                    replaced_bytes = fixes.restore_byte_a0(encoded_bytes)
                    if replaced_bytes != encoded_bytes:
                        transcode_steps.append(("transcode", "restore_byte_a0"))
                        encoded_bytes = replaced_bytes

                # Replace sequences where information has been lost
                if config.replace_lossy_sequences and encoding.startswith("sloppy"):
                    replaced_bytes = fixes.replace_lossy_sequences(encoded_bytes)
                    if replaced_bytes != encoded_bytes:
                        transcode_steps.append(("transcode", "replace_lossy_sequences"))
                        encoded_bytes = replaced_bytes

                if 0xED in encoded_bytes or 0xC0 in encoded_bytes:
                    decoding = "utf-8-variants"

                decode_step = ("decode", decoding)
                steps = [encode_step] + transcode_steps + [decode_step]
                fixed = encoded_bytes.decode(decoding)
                return fixed, steps

            except UnicodeDecodeError:
                pass

    # Look for a-hat-euro sequences that remain, and fix them in isolation.
    if config.decode_inconsistent_utf8 and chardata.UTF8_DETECTOR_RE.search(text):
        steps = [("apply", "decode_inconsistent_utf8")]
        fixed = fixes.decode_inconsistent_utf8(text)
        if fixed != text:
            return fixed, steps

    # The next most likely case is that this is Latin-1 that was intended to
    # be read as Windows-1252, because those two encodings in particular are
    # easily confused.
    if "latin-1" in possible_1byte_encodings:
        if "windows-1252" in possible_1byte_encodings:
            # This text is in the intersection of Latin-1 and
            # Windows-1252, so it's probably legit.
            return text, []
        else:
            # Otherwise, it means we have characters that are in Latin-1 but
            # not in Windows-1252. Those are C1 control characters. Nobody
            # wants those. Assume they were meant to be Windows-1252.
            try:
                fixed = text.encode("latin-1").decode("windows-1252")
                if fixed != text:
                    steps = [("encode", "latin-1"), ("decode", "windows-1252")]
                    return fixed, steps
            except UnicodeDecodeError:
                pass

    # Fix individual characters of Latin-1 with a less satisfying explanation
    if config.fix_c1_controls and chardata.C1_CONTROL_RE.search(text):
        steps = [("transcode", "fix_c1_controls")]
        fixed = fixes.fix_c1_controls(text)
        return fixed, steps

    # The cases that remain are mixups between two different single-byte
    # encodings, and not the common case of Latin-1 vs. Windows-1252.
    #
    # These cases may be unsolvable without adding false positives, though
    # I have vague ideas about how to optionally address them in the future.

    # Return the text unchanged; the plan is empty.
    return text, []


def fix_encoding(text, config=None, **kwargs):
    if config is None:
        config = TextFixerConfig()
    config = config._replace(**kwargs)
    fixed, explan = fix_encoding_and_explain(text, config)
    return fixed


# Some alternate names for the main functions
ftfy = fix_text


def fix_text_segment(text, config=None, **kwargs):
    warnings.warn(
        "`fix_text_segment()` is deprecated as of ftfy 6.0. "
        "Use `fix_and_explain()` instead.",
        DeprecationWarning,
    )

    if config is None:
        config = TextFixerConfig()
    config = config._replace(**kwargs)
    fixed, explan = fix_and_explain(text, config)
    return fixed


def fix_file(input_file, encoding=None, config=None):
    """
    Fix text that is found in a file.

    If the file is being read as Unicode text, use that. If it's being read as
    bytes, then we hope an encoding was supplied. If not, unfortunately, we
    have to guess what encoding it is. We'll try a few common encodings, but we
    make no promises. See the `guess_bytes` function for how this is done.

    The output is a stream of fixed lines of text.
    """
    for line in input_file:
        if isinstance(line, bytes):
            if encoding is None:
                line, encoding = guess_bytes(line)
            else:
                line = line.decode(encoding)
        if config.unescape_html == "auto" and "<" in line:
            config = config._replace(unescape_html=False)

        fixed_line, _explan = fix_and_explain(line, config)
        yield fixed_line


def guess_bytes(bstring):
    """
    NOTE: Using `guess_bytes` is not the recommended way of using ftfy. ftfy
    is not designed to be an encoding detector.

    In the unfortunate situation that you have some bytes in an unknown
    encoding, ftfy can guess a reasonable strategy for decoding them, by trying
    a few common encodings that can be distinguished from each other.

    Unlike the rest of ftfy, this may not be accurate, and it may *create*
    Unicode problems instead of solving them!

    The encodings we try here are:

    - UTF-16 with a byte order mark, because a UTF-16 byte order mark looks
      like nothing else
    - UTF-8, because it's the global standard, which has been used by a
      majority of the Web since 2008
    - "utf-8-variants", or buggy implementations of UTF-8
    - MacRoman, because Microsoft Office thinks it's still a thing, and it
      can be distinguished by its line breaks. (If there are no line breaks in
      the string, though, you're out of luck.)
    - Shift-JIS, the most common encoding of Japanese.
    - GB18030, a standardized encoding of Simplified Chinese.
    - Big5, a standardized encoding of Traditional Chinese.
    - "sloppy-windows-1252", the Latin-1-like encoding that is the most common
      single-byte encoding.
    """
    if isinstance(bstring, str):
        raise UnicodeError(
            "This string was already decoded as Unicode. You should pass "
            "bytes to guess_bytes, not Unicode."
        )

    if bstring.startswith(b"\xfe\xff") or bstring.startswith(b"\xff\xfe"):
        return bstring.decode("utf-16"), "utf-16"

    byteset = set(bstring)
    try:
        if 0xED in byteset or 0xC0 in byteset:
            # Byte 0xed can be used to encode a range of codepoints that
            # are UTF-16 surrogates. UTF-8 does not use UTF-16 surrogates,
            # so when we see 0xed, it's very likely we're being asked to
            # decode CESU-8, the variant that encodes UTF-16 surrogates
            # instead of the original characters themselves.
            #
            # This will occasionally trigger on standard UTF-8, as there
            # are some Korean characters that also use byte 0xed, but that's
            # not harmful because standard UTF-8 characters will decode the
            # same way in our 'utf-8-variants' codec.
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
            return bstring.decode("utf-8-variants"), "utf-8-variants"
        else:
            return bstring.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    # decode GB18030 text that contains either '人' or '日', or the sequence
    # that introduces many foreign Unicode characters, U+81 U+30.
    # (The U+81 U+30 sequence would appear, for example, in the GB18030 encoding
    # of UTF-8 mojibake.)
    try:
        if b"\xc8\xcb" in bstring or b"\xc8\xd5" in bstring or b"\x81\x30" in bstring:
            return bstring.decode("gb18030"), "gb18030"
    except UnicodeDecodeError:
        pass

    # decode Shift-JIS text that contains at least two of
    # [punctuation, hiragana, katakana], using bytes that are very uncommon outside
    # of UTF-8 and GB18030
    try:
        if (0x81 in byteset) + (0x82 in byteset) + (0x83 in byteset) >= 2:
            return bstring.decode("shift-jis"), "shift-jis"
    except UnicodeDecodeError:
        pass

    # decode Big5 text that contains either '人' or '日'
    try:
        if b"\xa4\x48" in bstring or b"\xa4\xe9" in bstring:
            return bstring.decode("big5"), "big5"
    except UnicodeDecodeError:
        pass

    if 0x0D in byteset and 0x0A not in byteset:
        # Files that contain CR and not LF are likely to be MacRoman.
        return bstring.decode("macroman"), "macroman"
    else:
        return bstring.decode("sloppy-windows-1252"), "sloppy-windows-1252"


def apply_plan(text, plan):
    """
    Apply a plan for fixing the encoding of text.

    The plan is a list of tuples of the form (operation, arg).

    `operation` is one of:

    - `'encode'`: convert a string to bytes, using `arg` as the encoding
    - `'decode'`: convert bytes to a string, using `arg` as the encoding
    - `'transcode'`: convert bytes to bytes, using the function named `arg`
    - `'apply'`: convert a string to a string, using the function named `arg`

    The functions that can be applied by 'transcode' and 'apply' appear in
    the dictionary named `FIXERS`.
    """
    obj = text
    for operation, encoding in plan:
        if operation == "encode":
            obj = obj.encode(encoding)
        elif operation == "decode":
            obj = obj.decode(encoding)
        elif operation == "transcode" or operation == "apply":
            if encoding in FIXERS:
                obj = FIXERS[encoding](obj)
            else:
                raise ValueError("Unknown function to apply: %s" % encoding)
        else:
            raise ValueError("Unknown plan step: %s" % operation)

    return obj


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
        U+FE35  ︵      [Ps] PRESENTATION FORM FOR VERTICAL LEFT PARENTHESIS
        U+0020          [Zs] SPACE
        U+253B  ┻       [So] BOX DRAWINGS HEAVY UP AND HORIZONTAL
        U+2501  ━       [So] BOX DRAWINGS HEAVY HORIZONTAL
        U+253B  ┻       [So] BOX DRAWINGS HEAVY UP AND HORIZONTAL
    """
    for char in text:
        if char.isprintable():
            display = char
        else:
            display = char.encode("unicode-escape").decode("ascii")
        print(
            "U+{code:04X}  {display} [{category}] {name}".format(
                display=display_ljust(display, 7),
                code=ord(char),
                category=unicodedata.category(char),
                name=unicodedata.name(char, "<unknown>"),
            )
        )
