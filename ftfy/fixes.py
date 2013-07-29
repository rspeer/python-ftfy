# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.chardata import (possible_encoding, CHARMAPS, CHARMAP_ENCODINGS,
                           CONTROL_CHARS)
from ftfy.badness import text_cost
import re
import sys

if sys.hexversion >= 0x03000000:
    from html import entities
    htmlentitydefs = entities
    unichr = chr
else:
    import htmlentitydefs


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
    """
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

    NOTE: the following examples are written using unmarked literal strings,
    but they are Unicode text. In Python 2 we have "unicode_literals" turned
    on, and in Python 3 this is always the case.

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
    \x81 that have no mapping in Windows.

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
    """
    while True:
        origtext = text
        text, _ = fix_text_and_explain(text)
        if text == origtext:
            return text

def fix_text_and_explain(text):
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
            # This is an ugly-looking way to get the bytes that represent
            # the text in this encoding. The reason we can't necessarily
            # use .encode(encoding) is that the decoder is very likely
            # to have been sloppier than Python.
            #
            # The decoder might have left bytes unchanged when they're not
            # part of the encoding. It might represent b'\x81' as u'\x81'
            # in Windows-1252, while Python would claim that using byte
            # 0x81 in Windows-1252 is an error.
            #
            # So what we do here is we use the .translate method of Unicode
            # strings. Using it with the character maps we have computed will 
            # give us back a Unicode string using only code
            # points up to 0xff. This can then be converted into the intended
            # bytes by encoding it as Latin-1.
            sorta_encoded_text = text.translate(CHARMAPS[encoding])
            encoded_bytes = sorta_encoded_text.encode('latin-1')

            # Now, find out if it's UTF-8.
            try:
                fixed = encoded_bytes.decode('utf-8')
                steps = [('sloppy_encode', encoding), ('decode', 'utf-8')]
                if text_cost(fixed) < text_cost(text):
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
            # wants those. Assume they were meant to be Windows-1252.
            encoded = text.encode('latin-1')
            fixed = encoded.decode('windows-1252', errors='replace')
            steps = [('encode', 'latin-1'), ('decode', 'windows-1252')]
            return fixed, steps

    # The cases that remain are mixups between two different single-byte
    # encodings, neither of which is Latin-1.
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


HTML_ENTITY_RE = re.compile("&#?\w+;")
def unescape_html(text):
    """
    Decode all three types of HTML entities/character references.

    Code by Fredrik Lundh of effbot.org.

        >>> print(unescape_html('&lt;tag&gt;'))
        <tag>
    """
    def fixup(m):
        text = m.group(0)
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


ANSI_RE = re.compile('\033\[((?:\d|;)*)([a-zA-Z])')
def remove_terminal_escapes(text):
    """
    Strip out "ANSI" terminal escape sequences, such as those that produce
    colored text on Unix.
    """
    return ANSI_RE.sub('', text)


SINGLE_QUOTE_RE = re.compile('[\u2018-\u201b]')
DOUBLE_QUOTE_RE = re.compile('[\u201c-\u201f]')
def uncurl_quotes(text):
    """
    Replace curly quotation marks with straight equivalents.

        >>> print(uncurl_quotes('\u201chere\u2019s a test\u201d'))
        "here's a test"
    """
    return SINGLE_QUOTE_RE.sub("'", DOUBLE_QUOTE_RE.sub('"', text))


def remove_control_chars(text):
    return text.translate(CONTROL_CHARS)


def remove_bom(text):
    """
    Remove a left-over byte-order mark.
    """
    return text.lstrip(unichr(0xfeff))
