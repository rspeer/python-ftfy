"""
This module contains the individual fixes that the main fix_text function
can perform.
"""

import codecs
import html
import re

from ftfy.chardata import (
    ALTERED_UTF8_RE,
    C1_CONTROL_RE,
    CHARMAP_ENCODINGS,
    CONTROL_CHARS,
    DOUBLE_QUOTE_RE,
    HTML_ENTITIES,
    HTML_ENTITY_RE,
    LIGATURES,
    LOSSY_UTF8_RE,
    SINGLE_QUOTE_RE,
    UTF8_DETECTOR_RE,
    WIDTH_MAP,
    badness,
    is_bad,
    possible_encoding,
)

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


def fix_encoding(text):
    r"""
    Fix text with incorrectly-decoded garbage ("mojibake") whenever possible.

    This function looks for the evidence of mojibake, formulates a plan to fix
    it, and applies the plan.  It determines whether it should replace nonsense
    sequences of single-byte characters that were really meant to be UTF-8
    characters, and if so, turns them into the correctly-encoded Unicode
    character that they were meant to represent.

    The input to the function must be Unicode. If you don't have Unicode text,
    you're not using the right tool to solve your problem.

    `fix_encoding` decodes text that looks like it was decoded incorrectly. It
    leaves alone text that doesn't.

        >>> fix_encoding('Ãºnico')
        'único'

        >>> fix_encoding('This text is fine already :þ')
        'This text is fine already :þ'

    Because these characters often come from Microsoft products, we allow
    for the possibility that we get not just Unicode characters 128-255, but
    also Windows's conflicting idea of what characters 128-160 are.

        >>> fix_encoding('This â€” should be an em dash')
        'This — should be an em dash'

    We might have to deal with both Windows characters and raw control
    characters at the same time, especially when dealing with characters like
    0x81 that have no mapping in Windows. This is a string that Python's
    standard `.encode` and `.decode` methods cannot correct.

        >>> fix_encoding('This text is sad .â\x81”.')
        'This text is sad .⁔.'

    However, it has safeguards against fixing sequences of letters and
    punctuation that can occur in valid text. In the following example,
    the last three characters are not replaced with a Korean character,
    even though they could be.

        >>> fix_encoding('not such a fan of Charlotte Brontë…”')
        'not such a fan of Charlotte Brontë…”'

    This function can now recover some complex manglings of text, such as when
    UTF-8 mojibake has been normalized in a way that replaces U+A0 with a
    space:

        >>> fix_encoding('The more you know ðŸŒ ')
        'The more you know 🌠'

    Cases of genuine ambiguity can sometimes be addressed by finding other
    characters that are not double-encoded, and expecting the encoding to
    be consistent:

        >>> fix_encoding('AHÅ™, the new sofa from IKEA®')
        'AHÅ™, the new sofa from IKEA®'

    Finally, we handle the case where the text is in a single-byte encoding
    that was intended as Windows-1252 all along but read as Latin-1:

        >>> fix_encoding('This text was never UTF-8 at all\x85')
        'This text was never UTF-8 at all…'

    The best version of the text is found using
    :func:`ftfy.badness.text_cost`.
    """
    text, _ = fix_encoding_and_explain(text)
    return text


def fix_encoding_and_explain(text):
    """
    Re-decodes text that has been decoded incorrectly, and also return a
    "plan" indicating all the steps required to fix it.

    The resulting plan could be used with :func:`ftfy.fixes.apply_plan`
    to fix additional strings that are broken in the same way.
    """
    if isinstance(text, bytes):
        raise UnicodeError(BYTES_ERROR_TEXT)

    plan_so_far = []
    while True:
        prevtext = text
        text, plan = fix_one_step_and_explain(text)
        plan_so_far.extend(plan)
        if text == prevtext:
            return text, plan_so_far


def fix_one_step_and_explain(text):
    """
    Performs a single step of re-decoding text that's been decoded incorrectly.

    Returns the decoded text, plus a "plan" for how to reproduce what it did.
    """
    if len(text) == 0:
        return text, []

    # The first plan is to return ASCII text unchanged, as well as text
    # that doesn't look like it contains mojibake
    if possible_encoding(text, 'ascii') or not is_bad(text):
        return text, []

    # As we go through the next step, remember the possible encodings
    # that we encounter but don't successfully fix yet. We may need them
    # later.
    possible_1byte_encodings = []

    # Suppose the text was supposed to be UTF-8, but it was decoded using
    # a single-byte encoding instead. When these cases can be fixed, they
    # are usually the correct thing to do, so try them next.
    for encoding in CHARMAP_ENCODINGS:
        if possible_encoding(text, encoding):
            possible_1byte_encodings.append(encoding)
            encoded_bytes = text.encode(encoding)
            encode_step = ('encode', encoding)
            transcode_steps = []

            # Now, find out if it's UTF-8 (or close enough). Otherwise,
            # remember the encoding for later.
            try:
                decoding = 'utf-8'
                # Check encoded_bytes for sequences that would be UTF-8,
                # except they have b' ' where b'\xa0' would belong.
                if ALTERED_UTF8_RE.search(encoded_bytes):
                    encoded_bytes = restore_byte_a0(encoded_bytes)
                    transcode_steps.append(('transcode', 'restore_byte_a0'))

                # Check for the byte 0x1a, which indicates where one of our
                # 'sloppy' codecs found a replacement character.
                if encoding.startswith('sloppy') and 0x1a in encoded_bytes:
                    encoded_bytes = replace_lossy_sequences(encoded_bytes)
                    transcode_steps.append(('transcode', 'replace_lossy_sequences'))

                if 0xed in encoded_bytes or 0xc0 in encoded_bytes:
                    decoding = 'utf-8-variants'

                decode_step = ('decode', decoding)
                steps = [encode_step] + transcode_steps + [decode_step]
                fixed = encoded_bytes.decode(decoding)
                return fixed, steps

            except UnicodeDecodeError:
                pass

    # Look for a-hat-euro sequences that remain, and fix them in isolation.
    if UTF8_DETECTOR_RE.search(text):
        steps = [('transcode', 'fix_inconsistent_utf8_mojibake')]
        fixed = fix_inconsistent_utf8_mojibake(text)
        if fixed != text:
            return fixed, steps

    # The next most likely case is that this is Latin-1 that was intended to
    # be read as Windows-1252, because those two encodings in particular are
    # easily confused.
    if 'latin-1' in possible_1byte_encodings:
        if 'windows-1252' in possible_1byte_encodings:
            # This text is in the intersection of Latin-1 and
            # Windows-1252, so it's probably legit.
            return text, []
        else:
            # Otherwise, it means we have characters that are in Latin-1 but
            # not in Windows-1252. Those are C1 control characters. Nobody
            # wants those. Assume they were meant to be Windows-1252.
            try:
                fixed = text.encode('latin-1').decode('windows-1252')
                if fixed != text:
                    steps = [('encode', 'latin-1'), ('decode', 'windows-1252')]
                    return fixed, steps
            except UnicodeDecodeError:
                pass

    # Fix individual characters of Latin-1 with a less satisfying explanation
    if C1_CONTROL_RE.search(text):
        steps = [('transcode', 'fix_c1_controls')]
        fixed = fix_c1_controls(text)
        return fixed, steps
    
    # The cases that remain are mixups between two different single-byte
    # encodings, and not the common case of Latin-1 vs. Windows-1252.
    #
    # These cases may be unsolvable without adding false positives, though
    # I have vague ideas about how to optionally address them in the future.

    # Return the text unchanged; the plan is empty.
    return text, []


def apply_plan(text, plan):
    """
    Apply a plan for fixing the encoding of text.

    The plan is a list of tuples of the form (operation, encoding):

    - `operation` is 'encode' if it turns a string into bytes, 'decode' if it
      turns bytes into a string, and 'transcode' if it keeps the type the same.
    - `encoding` is the name of the encoding to use, such as 'utf-8' or
      'latin-1', or the function name in the case of 'transcode'.
    """
    obj = text
    for operation, encoding in plan:
        if operation == 'encode':
            obj = obj.encode(encoding)
        elif operation == 'decode':
            obj = obj.decode(encoding)
        elif operation == 'transcode':
            if encoding in TRANSCODERS:
                obj = TRANSCODERS[encoding](obj)
            else:
                raise ValueError("Unknown transcode operation: %s" % encoding)
        else:
            raise ValueError("Unknown plan step: %s" % operation)

    return obj


def _unescape_fixup(match):
    """
    Replace one matched HTML entity with the character it represents,
    if possible.
    """
    text = match.group(0)
    if text in HTML_ENTITIES:
        return HTML_ENTITIES[text]
    elif text.startswith('&#'):
        unescaped = html.unescape(text)

        # If html.unescape only decoded part of the string, that's not what
        # we want. The semicolon should be consumed.
        if ';' in unescaped:
            return text
        else:
            return unescaped
    else:
        return text


def unescape_html(text):
    """
    Decode HTML entities and character references, including some nonstandard
    ones written in all-caps.

    Python has a built-in called `html.unescape` that can decode HTML escapes,
    including a bunch of messy edge cases such as decoding escapes without
    semicolons such as "&amp".

    If you know you've got HTML-escaped text, applying `html.unescape` is the
    right way to convert it to plain text. But in ambiguous situations, that
    would create false positives. For example, the informally written text
    "this&not that" should not automatically be decoded as "this¬ that".

    In this function, we decode the escape sequences that appear in the
    `html.entities.html5` dictionary, as long as they are the unambiguous ones
    that end in semicolons.

    We also decode all-caps versions of Latin letters and common symbols.
    If a database contains the name 'P&EACUTE;REZ', we can read that and intuit
    that it was supposed to say 'PÉREZ'. This is limited to a smaller set of
    entities, because there are many instances where entity names are
    case-sensitive in complicated ways.

        >>> unescape_html('&lt;tag&gt;')
        '<tag>'

        >>> unescape_html('&Jscr;ohn &HilbertSpace;ancock')
        '𝒥ohn ℋancock'

        >>> unescape_html('&checkmark;')
        '✓'

        >>> unescape_html('P&eacute;rez')
        'Pérez'

        >>> unescape_html('P&EACUTE;REZ')
        'PÉREZ'

        >>> unescape_html('BUNDESSTRA&SZLIG;E')
        'BUNDESSTRASSE'

        >>> unescape_html('&ntilde; &Ntilde; &NTILDE; &nTILDE;')
        'ñ Ñ Ñ &nTILDE;'
    """
    return HTML_ENTITY_RE.sub(_unescape_fixup, text)


ANSI_RE = re.compile('\033\\[((?:\\d|;)*)([a-zA-Z])')


def remove_terminal_escapes(text):
    r"""
    Strip out "ANSI" terminal escape sequences, such as those that produce
    colored text on Unix.

        >>> print(remove_terminal_escapes(
        ...     "\033[36;44mI'm blue, da ba dee da ba doo...\033[0m"
        ... ))
        I'm blue, da ba dee da ba doo...
    """
    return ANSI_RE.sub('', text)


def uncurl_quotes(text):
    r"""
    Replace curly quotation marks with straight equivalents.

        >>> print(uncurl_quotes('\u201chere\u2019s a test\u201d'))
        "here's a test"
    """
    return SINGLE_QUOTE_RE.sub("'", DOUBLE_QUOTE_RE.sub('"', text))


def fix_latin_ligatures(text):
    """
    Replace single-character ligatures of Latin letters, such as 'ﬁ', with the
    characters that they contain, as in 'fi'. Latin ligatures are usually not
    intended in text strings (though they're lovely in *rendered* text).  If
    you have such a ligature in your string, it is probably a result of a
    copy-and-paste glitch.

    We leave ligatures in other scripts alone to be safe. They may be intended,
    and removing them may lose information. If you want to take apart nearly
    all ligatures, use NFKC normalization.

        >>> print(fix_latin_ligatures("ﬂuﬃeﬆ"))
        fluffiest
    """
    return text.translate(LIGATURES)


def fix_character_width(text):
    """
    The ASCII characters, katakana, and Hangul characters have alternate
    "halfwidth" or "fullwidth" forms that help text line up in a grid.

    If you don't need these width properties, you probably want to replace
    these characters with their standard form, which is what this function
    does.

    Note that this replaces the ideographic space, U+3000, with the ASCII
    space, U+20.

        >>> print(fix_character_width("ＬＯＵＤ　ＮＯＩＳＥＳ"))
        LOUD NOISES
        >>> print(fix_character_width("Ｕﾀｰﾝ"))   # this means "U-turn"
        Uターン
    """
    return text.translate(WIDTH_MAP)


def fix_line_breaks(text):
    r"""
    Convert all line breaks to Unix style.

    This will convert the following sequences into the standard \\n
    line break:

        - CRLF (\\r\\n), used on Windows and in some communication
          protocols
        - CR (\\r), once used on Mac OS Classic, and now kept alive
          by misguided software such as Microsoft Office for Mac
        - LINE SEPARATOR (\\u2028) and PARAGRAPH SEPARATOR (\\u2029),
          defined by Unicode and used to sow confusion and discord
        - NEXT LINE (\\x85), a C1 control character that is certainly
          not what you meant

    The NEXT LINE character is a bit of an odd case, because it
    usually won't show up if `fix_encoding` is also being run.
    \\x85 is very common mojibake for \\u2026, HORIZONTAL ELLIPSIS.

        >>> print(fix_line_breaks(
        ...     "This string is made of two things:\u2029"
        ...     "1. Unicode\u2028"
        ...     "2. Spite"
        ... ))
        This string is made of two things:
        1. Unicode
        2. Spite

    For further testing and examples, let's define a function to make sure
    we can see the control characters in their escaped form:

        >>> def eprint(text):
        ...     print(text.encode('unicode-escape').decode('ascii'))

        >>> eprint(fix_line_breaks("Content-type: text/plain\r\n\r\nHi."))
        Content-type: text/plain\n\nHi.

        >>> eprint(fix_line_breaks("This is how Microsoft \r trolls Mac users"))
        This is how Microsoft \n trolls Mac users

        >>> eprint(fix_line_breaks("What is this \x85 I don't even"))
        What is this \n I don't even
    """
    return (
        text.replace('\r\n', '\n')
        .replace('\r', '\n')
        .replace('\u2028', '\n')
        .replace('\u2029', '\n')
        .replace('\u0085', '\n')
    )


SURROGATE_RE = re.compile('[\ud800-\udfff]')
SURROGATE_PAIR_RE = re.compile('[\ud800-\udbff][\udc00-\udfff]')


def convert_surrogate_pair(match):
    """
    Convert a surrogate pair to the single codepoint it represents.

    This implements the formula described at:
    http://en.wikipedia.org/wiki/Universal_Character_Set_characters#Surrogates
    """
    pair = match.group(0)
    codept = 0x10000 + (ord(pair[0]) - 0xd800) * 0x400 + (ord(pair[1]) - 0xdc00)
    return chr(codept)


def fix_surrogates(text):
    """
    Replace 16-bit surrogate codepoints with the characters they represent
    (when properly paired), or with \ufffd otherwise.

        >>> high_surrogate = chr(0xd83d)
        >>> low_surrogate = chr(0xdca9)
        >>> print(fix_surrogates(high_surrogate + low_surrogate))
        💩
        >>> print(fix_surrogates(low_surrogate + high_surrogate))
        ��

    The above doctest had to be very carefully written, because even putting
    the Unicode escapes of the surrogates in the docstring was causing
    various tools to fail, which I think just goes to show why this fixer is
    necessary.
    """
    if SURROGATE_RE.search(text):
        text = SURROGATE_PAIR_RE.sub(convert_surrogate_pair, text)
        text = SURROGATE_RE.sub('\ufffd', text)
    return text


def remove_control_chars(text):
    """
    Remove various control characters that you probably didn't intend to be in
    your text. Many of these characters appear in the table of "Characters not
    suitable for use with markup" at
    http://www.unicode.org/reports/tr20/tr20-9.html.

    This includes:

    - ASCII control characters, except for the important whitespace characters
      (U+00 to U+08, U+0B, U+0E to U+1F, U+7F)
    - Deprecated Arabic control characters (U+206A to U+206F)
    - Interlinear annotation characters (U+FFF9 to U+FFFB)
    - The Object Replacement Character (U+FFFC)
    - The byte order mark (U+FEFF)

    However, these similar characters are left alone:

    - Control characters that produce whitespace (U+09, U+0A, U+0C, U+0D,
      U+2028, and U+2029)
    - C1 control characters (U+80 to U+9F) -- even though they are basically
      never used intentionally, they are important clues about what mojibake
      has happened
    - Control characters that affect glyph rendering, such as joiners and
      right-to-left marks (U+200C to U+200F, U+202A to U+202E)
    - Musical notation control characters (U+1D173 to U+1D17A) because wow if
      you're using those you probably have a good reason
    - Tag characters, because they are now used in emoji sequences such as
      "Flag of Wales"
    """
    return text.translate(CONTROL_CHARS)


def remove_bom(text):
    r"""
    Remove a byte-order mark that was accidentally decoded as if it were part
    of the text.

    >>> print(remove_bom(chr(0xfeff) + "Where do you want to go today?"))
    Where do you want to go today?
    """
    return text.lstrip(chr(0xfeff))


# Define a regex to match valid escape sequences in Python string literals.
ESCAPE_SEQUENCE_RE = re.compile(
    r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''',
    re.UNICODE | re.VERBOSE,
)


def decode_escapes(text):
    r"""
    Decode backslashed escape sequences, including \\x, \\u, and \\U character
    references, even in the presence of other Unicode.

    This is what Python's "string-escape" and "unicode-escape" codecs were
    meant to do, but in contrast, this actually works. It will decode the
    string exactly the same way that the Python interpreter decodes its string
    literals.

        >>> factoid = '\\u20a1 is the currency symbol for the colón.'
        >>> print(factoid[1:])
        u20a1 is the currency symbol for the colón.
        >>> print(decode_escapes(factoid))
        ₡ is the currency symbol for the colón.

    Even though Python itself can read string literals with a combination of
    escapes and literal Unicode -- you're looking at one right now -- the
    "unicode-escape" codec doesn't work on literal Unicode. (See
    http://stackoverflow.com/a/24519338/773754 for more details.)

    Instead, this function searches for just the parts of a string that
    represent escape sequences, and decodes them, leaving the rest alone. All
    valid escape sequences are made of ASCII characters, and this allows
    "unicode-escape" to work correctly.

    This fix cannot be automatically applied by the `ftfy.fix_text` function,
    because escaped text is not necessarily a mistake, and there is no way
    to distinguish text that's supposed to be escaped from text that isn't.
    """

    def decode_match(match):
        "Given a regex match, decode the escape sequence it contains."
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, text)


# This regex implements an exception to restore_byte_a0, so we can decode the
# very common mojibake of (for example) "Ã la mode" as "à la mode", not "àla
# mode".
#
# If byte C3 appears with a single space after it -- most commonly this shows
# up as " Ã " appearing as an entire word -- we'll insert \xa0 while keeping
# the space. Without this change, we would decode "à" as the start of the next
# word, such as "àla". It's almost always intended to be a separate word, as in
# "à la", but when mojibake turns this into "Ã\xa0 la", the two kinds of spaces
# get coalesced into "Ã la".
#
# We make exceptions for the Portuguese words "às", "àquele", "àquela",
# "àquilo" and their plurals -- these are contractions of, for example, "a
# aquele" and are very common. Note that the final letter is important to
# distinguish this case from French "à quel point".
#
# Other instances in Portuguese, such as "àfrica", seem to be typos (intended
# to be "África" with the accent in the other direction).
#
# Unfortunately, "à" is a common letter in Catalan, and mojibake of words that
# contain it will end up with inserted spaces. We can't do the right thing with
# every word. The cost is that the mojibake text "fÃ cil" will be interpreted as
# "fà cil", not "fàcil".
A_GRAVE_WORD_RE = re.compile(b'\xc3 (?! |quele|quela|quilo|s )')

def restore_byte_a0(byts):
    """
    Some mojibake has been additionally altered by a process that said "hmm,
    byte A0, that's basically a space!" and replaced it with an ASCII space.
    When the A0 is part of a sequence that we intend to decode as UTF-8,
    changing byte A0 to 20 would make it fail to decode.

    This process finds sequences that would convincingly decode as UTF-8 if
    byte 20 were changed to A0, and puts back the A0. For the purpose of
    deciding whether this is a good idea, this step gets a cost of twice
    the number of bytes that are changed.

    This is used as a step within `fix_encoding`.
    """
    byts = A_GRAVE_WORD_RE.sub(b'\xc3\xa0 ', byts)

    def replacement(match):
        "The function to apply when this regex matches."
        return match.group(0).replace(b'\x20', b'\xa0')

    return ALTERED_UTF8_RE.sub(replacement, byts)


def replace_lossy_sequences(byts):
    """
    This function identifies sequences where information has been lost in
    a "sloppy" codec, indicated by byte 1A, and if they would otherwise look
    like a UTF-8 sequence, it replaces them with the UTF-8 sequence for U+FFFD.

    A further explanation:

    ftfy can now fix text in a few cases that it would previously fix
    incompletely, because of the fact that it can't successfully apply the fix
    to the entire string. A very common case of this is when characters have
    been erroneously decoded as windows-1252, but instead of the "sloppy"
    windows-1252 that passes through unassigned bytes, the unassigned bytes get
    turned into U+FFFD (�), so we can't tell what they were.

    This most commonly happens with curly quotation marks that appear
    ``â€œ like this â€�``.

    We can do better by building on ftfy's "sloppy codecs" to let them handle
    less-sloppy but more-lossy text. When they encounter the character ``�``,
    instead of refusing to encode it, they encode it as byte 1A -- an
    ASCII control code called SUBSTITUTE that once was meant for about the same
    purpose. We can then apply a fixer that looks for UTF-8 sequences where
    some continuation bytes have been replaced by byte 1A, and decode the whole
    sequence as �; if that doesn't work, it'll just turn the byte back into �
    itself.

    As a result, the above text ``â€œ like this â€�`` will decode as
    ``“ like this �``.

    If U+1A was actually in the original string, then the sloppy codecs will
    not be used, and this function will not be run, so your weird control
    character will be left alone but wacky fixes like this won't be possible.

    This is used as a transcoder within `fix_encoding`.
    """
    return LOSSY_UTF8_RE.sub('\ufffd'.encode('utf-8'), byts)

    
def fix_inconsistent_utf8_mojibake(text):
    """
    Sometimes, text from one encoding ends up embedded within text from a
    different one. This is common enough that we need to be able to fix it.

    This is used as a transcoder within `fix_encoding`.
    """

    def fix_embedded_mojibake(match):
        substr = match.group(0)
        
        # Require the match to be shorter, so that this doesn't recurse infinitely
        if len(substr) < len(text) and is_bad(substr):
            return fix_encoding(substr)
        else:
            return substr
    
    return UTF8_DETECTOR_RE.sub(fix_embedded_mojibake, text)


def _c1_fixer(match):
    return match.group(0).encode('latin-1').decode('sloppy-windows-1252')


def fix_c1_controls(text):
    """
    If text still contains C1 control characters, treat them as their
    Windows-1252 equivalents. This matches what Web browsers do.
    """
    return C1_CONTROL_RE.sub(_c1_fixer, text)


TRANSCODERS = {
    'restore_byte_a0': restore_byte_a0,
    'replace_lossy_sequences': replace_lossy_sequences,
    'fix_inconsistent_utf8_mojibake': fix_inconsistent_utf8_mojibake,
    'fix_c1_controls': fix_c1_controls
}
