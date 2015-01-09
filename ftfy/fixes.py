# -*- coding: utf-8 -*-
"""
This module contains the individual fixes that the main fix_text function
can perform.
"""

from __future__ import unicode_literals
from ftfy.chardata import (possible_encoding,
                           CHARMAP_ENCODINGS, CONTROL_CHARS)
from ftfy.badness import text_cost
from ftfy.compatibility import htmlentitydefs, unichr, UNSAFE_PRIVATE_USE_RE
import re
import sys
import codecs
import warnings


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

    http://docs.python.org/%d/howto/unicode.html
""" % sys.version_info[0]


def fix_text_encoding(text):
    r"""
    Fix text with incorrectly-decoded garbage ("mojibake") whenever possible.

    Something you will find all over the place, in real-world text, is text
    that's mistakenly encoded as utf-8, decoded in some ugly format like
    latin-1 or even Windows codepage 1252, and encoded as utf-8 again.

    This causes your perfectly good Unicode-aware code to end up with garbage
    text because someone else (or maybe "someone else") made a mistake.

    This function looks for the evidence of that having happened and fixes it.
    It determines whether it should replace nonsense sequences of single-byte
    characters that were really meant to be UTF-8 characters, and if so, turns
    them into the correctly-encoded Unicode character that they were meant to
    represent.

    The input to the function must be Unicode. If you don't have Unicode text,
    you're not using the right tool to solve your problem.

    .. note::
        The following examples are written using unmarked literal strings,
        but they are Unicode text. In Python 2 we have "unicode_literals"
        turned on, and in Python 3 this is always the case.

    ftfy decodes text that looks like it was decoded incorrectly. It leaves
    alone text that doesn't.

        >>> print(fix_text_encoding('Ãºnico'))
        único

        >>> print(fix_text_encoding('This text is fine already :þ'))
        This text is fine already :þ

    Because these characters often come from Microsoft products, we allow
    for the possibility that we get not just Unicode characters 128-255, but
    also Windows's conflicting idea of what characters 128-160 are.

        >>> print(fix_text_encoding('This â€” should be an em dash'))
        This — should be an em dash

    We might have to deal with both Windows characters and raw control
    characters at the same time, especially when dealing with characters like
    0x81 that have no mapping in Windows. This is a string that Python's
    standard `.encode` and `.decode` methods cannot correct.

        >>> print(fix_text_encoding('This text is sad .â\x81”.'))
        This text is sad .⁔.

    However, it has safeguards against fixing sequences of letters and
    punctuation that can occur in valid text:

        >>> print(fix_text_encoding('not such a fan of Charlotte Brontë…”'))
        not such a fan of Charlotte Brontë…”

    Cases of genuine ambiguity can sometimes be addressed by finding other
    characters that are not double-encoded, and expecting the encoding to
    be consistent:

        >>> print(fix_text_encoding('AHÅ™, the new sofa from IKEA®'))
        AHÅ™, the new sofa from IKEA®

    Finally, we handle the case where the text is in a single-byte encoding
    that was intended as Windows-1252 all along but read as Latin-1:

        >>> print(fix_text_encoding('This text was never UTF-8 at all\x85'))
        This text was never UTF-8 at all…

    The best version of the text is found using
    :func:`ftfy.badness.text_cost`.
    """
    text, _plan = fix_encoding_and_explain(text)
    return text


def fix_encoding_and_explain(text):
    """
    Re-decodes text that has been decoded incorrectly, and also return a
    "plan" indicating all the steps required to fix it.

    To fix similar text in the same way, without having to detect anything,
    you can use the ``apply_plan`` function.
    """
    best_version = text
    best_cost = text_cost(text)
    best_plan = []
    plan_so_far = []
    while True:
        prevtext = text
        text, plan = fix_one_step_and_explain(text)
        plan_so_far.extend(plan)
        cost = text_cost(text)

        # Add a penalty if we used a particularly obsolete encoding. The result
        # is that we won't use these encodings unless they can successfully
        # replace multiple characters.
        if ('encode', 'macroman') in plan_so_far or\
           ('encode', 'cp437') in plan_so_far:
            cost += 2

        # We need pretty solid evidence to decode from Windows-1251 (Cyrillic).
        if ('encode', 'sloppy-windows-1251') in plan_so_far:
            cost += 5

        if cost < best_cost:
            best_cost = cost
            best_version = text
            best_plan = list(plan_so_far)
        if text == prevtext:
            return best_version, best_plan


def fix_one_step_and_explain(text):
    """
    Performs a single step of re-decoding text that's been decoded incorrectly.

    Returns the decoded text, plus a "plan" for how to reproduce what it
    did.
    """
    if isinstance(text, bytes):
        raise UnicodeError(BYTES_ERROR_TEXT)
    if len(text) == 0:
        return text, []

    # The first plan is to return ASCII text unchanged.
    if possible_encoding(text, 'ascii'):
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
            encoded_bytes = text.encode(encoding)

            # Now, find out if it's UTF-8 (or close enough). Otherwise,
            # remember the encoding for later.
            try:
                decoding = 'utf-8'
                if b'\xed' in encoded_bytes or b'\xc0' in encoded_bytes:
                    decoding = 'utf-8-variants'
                fixed = encoded_bytes.decode(decoding)
                steps = [('encode', encoding), ('decode', decoding)]
                return fixed, steps
            except UnicodeDecodeError:
                possible_1byte_encodings.append(encoding)

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
            # wants those. Assume they were meant to be Windows-1252. Don't
            # use the sloppy codec, because bad Windows-1252 characters are
            # a bad sign.
            encoded = text.encode('latin-1')
            try:
                fixed = encoded.decode('windows-1252')
                steps = []
                if fixed != text:
                    steps = [('encode', 'latin-1'), ('decode', 'windows-1252')]
                return fixed, steps
            except UnicodeDecodeError:
                # This text contained characters that don't even make sense
                # if you assume they were supposed to be Windows-1252. In
                # that case, let's not assume anything.
                pass

    # The cases that remain are mixups between two different single-byte
    # encodings, and not the common case of Latin-1 vs. Windows-1252.
    #
    # Those cases are somewhat rare, and impossible to solve without false
    # positives. If you're in one of these situations, you should try using
    # the `ftfy.guess_bytes` function.

    # Return the text unchanged; the plan is empty.
    return text, []


def apply_plan(text, plan):
    """
    Apply a plan for fixing the encoding of text.

    The plan is a list of tuples of the form (operation, encoding), where
    `operation` is either 'encode' or 'decode', and `encoding` is an encoding
    name such as 'utf-8' or 'latin-1'.

    Because only text can be encoded, and only bytes can be decoded, the plan
    should alternate 'encode' and 'decode' steps, or else this function will
    encounter an error.
    """
    obj = text
    for operation, encoding in plan:
        if operation == 'encode':
            obj = obj.encode(encoding)
        elif operation == 'decode':
            obj = obj.decode(encoding)
        else:
            raise ValueError("Unknown plan step: %s" % operation)

    return obj


HTML_ENTITY_RE = re.compile(r"&#?\w{0,8};")


def unescape_html(text):
    """
    Decode all three types of HTML entities/character references.

    Code by Fredrik Lundh of effbot.org. Rob Speer made a slight change
    to it for efficiency: it won't match entities longer than 8 characters,
    because there are no valid entities like that.

        >>> print(unescape_html('&lt;tag&gt;'))
        <tag>
    """
    def fixup(match):
        """
        Replace one matched HTML entity with the character it represents,
        if possible.
        """
        text = match.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return HTML_ENTITY_RE.sub(fixup, text)


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


SINGLE_QUOTE_RE = re.compile('[\u2018-\u201b]')
DOUBLE_QUOTE_RE = re.compile('[\u201c-\u201f]')

def uncurl_quotes(text):
    r"""
    Replace curly quotation marks with straight equivalents.

        >>> print(uncurl_quotes('\u201chere\u2019s a test\u201d'))
        "here's a test"
    """
    return SINGLE_QUOTE_RE.sub("'", DOUBLE_QUOTE_RE.sub('"', text))


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
    return text.replace('\r\n', '\n').replace('\r', '\n')\
               .replace('\u2028', '\n').replace('\u2029', '\n')\
               .replace('\u0085', '\n')


SURROGATE_RE = re.compile('[\ud800-\udfff]')
SURROGATE_PAIR_RE = re.compile('[\ud800-\udbff][\udc00-\udfff]')


def convert_surrogate_pair(match):
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
    Remove all control characters except for the important ones.

    This removes characters in these ranges:

    - U+0000 to U+0008
    - U+000B
    - U+000E to U+001F
    - U+007F

    It leaves alone these characters that are commonly used for formatting:

    - TAB (U+0009)
    - LF (U+000A)
    - FF (U+000C)
    - CR (U+000D)
    """
    return text.translate(CONTROL_CHARS)


def remove_bom(text):
    r"""
    Remove a left-over byte-order mark.

    >>> print(remove_bom("\ufeffWhere do you want to go today?"))
    Where do you want to go today?
    """
    return text.lstrip(unichr(0xfeff))


def remove_unsafe_private_use(text):
    r"""
    This function is deprecated, because the Python bug it works around has
    been fixed for a long time. It only affects old versions of Python that
    are also insecure in more serious ways.

    Certain string operations would crash Python < 3.3.3 and < 2.7.6 with a
    SystemError: http://bugs.python.org/issue18183

    ftfy's solution was to remove all characters from Supplementary Private
    Use Area B, using a regex that is known not to crash given those
    characters. In retrospect, it would have been a better idea to indicate
    that they were replaced, using the Unicode replacement character \ufffd.

        >>> print(remove_unsafe_private_use('\U0001F4A9\U00100000'))
        💩
    
    ftfy no longer applies this fix, and it will be removed in ftfy 3.5.
    """
    warnings.warn(
        "remove_unsafe_private_use is deprecated and will be removed in "
        "ftfy 3.5",
        DeprecationWarning
    )
    return UNSAFE_PRIVATE_USE_RE.sub('', text)


# Define a regex to match valid escape sequences in Python string literals.
ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)


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
