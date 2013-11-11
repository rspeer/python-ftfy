# -*- coding: utf-8 -*-
"""
This module contains the individual fixes that the main fix_text function
can perform.
"""

from __future__ import unicode_literals
from ftfy.chardata import (possible_encoding,
                           CHARMAP_ENCODINGS, CONTROL_CHARS)
from ftfy.badness import text_cost
from ftfy.compatibility import (htmlentitydefs, unichr, bytes_to_ints,
                                UNSAFE_PRIVATE_USE_RE)
import ftfy.bad_codecs
import re
import sys


BYTES_ERROR_TEXT = """Hey wait, this isn't Unicode.

ftfy is designed to fix problems that were introduced by handling Unicode
incorrectly. It might be able to fix the bytes you just handed it, but the
fact that you just gave a pile of bytes to a function that fixes text means
that your code is *also* handling Unicode incorrectly.

ftfy takes Unicode text as input. You should take these bytes and decode
them from the encoding you think they are in. If you're not sure, you can
try decoding it as 'latin-1' and letting ftfy take it from there. This may
or may not work, but at least it shouldn't make the situation worse.

If you're confused by this, please read the Python Unicode HOWTO:

    http://docs.python.org/%d/howto/unicode.html
""" % sys.version_info[0]


def fix_text_encoding(text):
    r"""
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
        but they are Unicode text. In Python 2 we have "unicode_literals" turned
        on, and in Python 3 this is always the case.

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
    \x81 that have no mapping in Windows. This is a string that Python's
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
    best_version = text
    best_cost = text_cost(text)
    plan_so_far = []
    while True:
        prevtext = text
        text, plan = fix_text_and_explain(text)
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
        if text == prevtext:
            return best_version

def fix_text_and_explain(text):
    """
    Performs a single step of re-encoding text that's been decoded incorrectly.
    It returns the decoded text, plus a structure explaining what it did.

    This structure could be used for more than it currently is, but we at least
    use it to track whether we had to intepret text as an old encoding such as
    MacRoman or cp437.
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
    #
    # We don't need to check for possibilities such as Latin-1 that was
    # intended to be read as MacRoman, because it is unlikely that any
    # software has that confusion.
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
    # positives. If you're in one of these situations, you don't need an
    # encoding fixer. You need something that heuristically guesses what
    # the encoding is in the first place.
    #
    # It's a different problem, the one that the 'chardet' module is
    # theoretically designed to solve. It probably *won't* solve it in
    # such an ambiguous case, but perhaps a version of it with better
    # heuristics would. Anyway, ftfy should not claim to solve it.

    return text, [('give up', None)]


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
    Convert line breaks to Unix style.

    In particular, this replaces CRLF (\\r\\n) with LF (\\n), then
    additionally replaces CR (\\r) with LF (\\n).
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')


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

    >>> print(remove_bom(unichr(0xfeff) + "Where do you want to go today?"))
    Where do you want to go today?
    """
    return text.lstrip(unichr(0xfeff))

def remove_unsafe_private_use(text):
    r"""
    Python 3.3's Unicode support isn't perfect, and in fact there are certain
    string operations that will crash it with a SystemError:
    http://bugs.python.org/issue18183

    You can trigger the bug by running `` '\U00010000\U00100000'.lower() ``.

    The best solution on Python 3.3 is to remove all characters from
    Supplementary Private Use Area B, using a regex that is known not to crash
    given those characters.
    
    These are the characters from U+100000 to U+10FFFF. It's sad to lose an
    entire plane of Unicode, but on the other hand, these characters are not
    assigned and never will be. If you get one of these characters and don't
    know what its purpose is, its purpose is probably to crash your code.
    
    If you were using these for actual private use, this might be inconvenient.
    You can turn off this fixer, of course, but I kind of encourage using
    Supplementary Private Use Area A instead.

        >>> print(remove_unsafe_private_use('\U0001F4A9\U00100000'))
        💩
    """
    return UNSAFE_PRIVATE_USE_RE.sub('', text)

