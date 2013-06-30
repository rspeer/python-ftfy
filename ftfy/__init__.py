# -*- coding: utf-8 -*-
"""
ftfy: fixes text for you

This is a module for making text less broken. See the `fix_text` function
for more information.
"""

from __future__ import unicode_literals

import unicodedata
import re
import sys
from ftfy.chardata import possible_encoding, CHARMAPS, CHARMAP_ENCODINGS

# Adjust names that have changed in Python 3
if sys.hexversion >= 0x03000000:
    from html import entities
    htmlentitydefs = entities
    unichr = chr
else:
    import htmlentitydefs


# Is this the right name?
def fix_text_encoding(text):
    """
    TODO documentation.

    Returns a fixed version of the text, plus a data structure that
    explains how it was fixed.
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
            # strings, which gives us back a Unicode string using only code
            # points up to 0xff. This can then be converted into the intended
            # bytes by encoding it as Latin-1.
            sorta_encoded_text = text.translate(CHARMAPS[encoding])
            encoded_bytes = sorta_encoded_text.encode('latin-1')

            # Now, find out if it's UTF-8.
            try:
                fixed = encoded_bytes.decode('utf-8')
                steps = [('sloppy_encode', encoding), ('decode', 'utf-8')]
                return fixed, steps
            except UnicodeDecodeError:
                possible_1byte_encodings.append(encoding)

    # The next most likely case is that this is Latin-1 that was intended to
    # be read as Windows-1252, because those two encodings in particular are
    # easily confused.
    #
    # We don't need to check for possibilites such as Latin-1 that was
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
            # wants those.
            encoded = text.encode('latin-1')
            fixed = encoded.decode('windows-1252', errors='replace')
            steps = [('encode', 'latin-1'), ('decode', 'windows-1252')]
            return fixed, steps

    # Now we need to check for a mixup between Windows-1252, cp437,
    # and MacRoman. We know Latin-1 isn't in the list, because if it were,
    # we would have returned already.
    #
    # We aren't crazy enough to try to turn text *into* Windows-1251.
    # Russia, if you screw things up that much, you're on you're own.
    for encoding in possible_1byte_encodings:
        for target in ['windows-1252', 'cp437', 'macroman']:
            result, goodness = try_reencoding(text, encoding, target)

            # A sort of prior: if it's not Windows-1252, it's less likely
            if target != 'windows-1252':
                goodness -= 5
            if goodness > 0:
                fixed = text.encode(encoding).decode(target)
                steps = [('encode', encoding), ('decode', target)]
                return fixed, steps

    # We haven't returned anything by now? That's probably fine. It means
    # this is probably perfectly good Unicode.
    return text, []


def fix_bad_encoding(text):
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

        >>> print(fix_bad_encoding('Ãºnico'))
        único

        >>> print(fix_bad_encoding('This text is fine already :þ'))
        This text is fine already :þ

    Because these characters often come from Microsoft products, we allow
    for the possibility that we get not just Unicode characters 128-255, but
    also Windows's conflicting idea of what characters 128-160 are.

        >>> print(fix_bad_encoding('This â€” should be an em dash'))
        This — should be an em dash

    We might have to deal with both Windows characters and raw control
    characters at the same time, especially when dealing with characters like
    \x81 that have no mapping in Windows.

        >>> print(fix_bad_encoding('This text is sad .â\x81”.'))
        This text is sad .⁔.

    This function even fixes multiple levels of badness:

        >>> wtf = '\xc3\xa0\xc2\xb2\xc2\xa0_\xc3\xa0\xc2\xb2\xc2\xa0'
        >>> print(fix_bad_encoding(wtf))
        ಠ_ಠ

    However, it has safeguards against fixing sequences of letters and
    punctuation that can occur in valid text:

        >>> print(fix_bad_encoding('not such a fan of Charlotte Brontë…”'))
        not such a fan of Charlotte Brontë…”

    Cases of genuine ambiguity can sometimes be addressed by finding other
    characters that are not double-encoded, and expecting the encoding to
    be consistent:

        >>> print(fix_bad_encoding('AHÅ™, the new sofa from IKEA®'))
        AHÅ™, the new sofa from IKEA®

    Finally, we handle the case where the text is in a single-byte encoding
    that was intended as Windows-1252 all along but read as Latin-1:

        >>> print(fix_bad_encoding('This text was never UTF-8 at all\x85'))
        This text was never UTF-8 at all…
    """
    keep_going = True
    while keep_going:
        fixed, info = fix_text_encoding(text)
        keep_going = (fixed != text)
        text = fixed

    return fixed


# ----------------
# Don't try to ftfy more than 64 KiB of text at a time, to prevent
# denial of service.
MAXLEN = 0x10000
BYTES_ERROR_TEXT = """Hey wait, this isn't Unicode!

ftfy is designed to fix problems that were introduced by handling Unicode
incorrectly. It might be able to fix the bytes you just handed it, but the
fact that you just gave a pile of bytes to a function that fixes text means
that your code is *also* handling Unicode incorrectly.

ftfy takes Unicode text as input. You should take these bytes and decode
them from the encoding you think they are in. If you're not sure, you can
try decoding it as 'latin-1', which may work and at least won't make
anything worse.

If you're confused by this, please read the Python Unicode HOWTO:

    http://docs.python.org/%d/howto/unicode.html
""" % sys.version_info[0]


def fix_text(text, normalization='NFKC'):
    """
    Given Unicode text as input, make its representation consistent and
    possibly less broken:

    - Detect whether the text was incorrectly encoded into UTF-8 and fix it,
      as defined in `fix_bad_encoding`.
    - If the text is HTML-escaped but has no HTML tags, replace HTML entities
      with their equivalent characters.
    - Remove terminal escapes and color codes.
    - Remove control characters except for newlines and tabs.
    - Normalize it with Unicode normalization form KC, which applies the
      following relevant transformations:
      - Combine characters and diacritics that are written using separate
        code points, such as converting "e" plus an acute accent modifier
        into "é", or converting "ka" (か) plus a dakuten into the
        single character "ga" (が).
      - Replace characters that are functionally equivalent with the most
        common form: for example, half-width katakana will be replaced with
        full-width, full-width Roman characters will be replaced with
        ASCII characters, ellipsis characters will be replaced by three
        periods, and the ligature 'ﬂ' will be replaced by 'fl'.
    - Replace curly quotation marks with straight ones.
    - Remove the Byte-Order Mark if it exists.

    You may change the `normalization` argument to apply a different kind of
    Unicode normalization, such as NFC or NFKD, or set it to None to skip this
    step.

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
    entities = True
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
            entities = False

        out.append(fix_text_segment(substring, normalization, entities))
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


def fix_text_segment(text, normalization='NFKC', entities=True):
    """
    Apply fixes to text in a single chunk. This could be a line of text
    within a larger run of `fix_text`, or it could be a larger amount
    of text that you are certain is all in the same encoding.
    """
    if isinstance(text, bytes):
        raise UnicodeError(BYTES_ERROR_TEXT)
    text = remove_terminal_escapes(text)
    if entities:
        text = unescape_html(text)
    text = fix_bad_encoding(text)
    text = text.translate(CONTROL_CHARS)
    if normalization is not None:
        text = unicodedata.normalize(normalization, text)
    text = uncurl_quotes(text)
    text = remove_bom(text)
    return text




def reinterpret_latin1_as_utf8(wrongtext):
    newbytes = wrongtext.encode('latin-1', 'replace')
    return newbytes.decode('utf-8', 'replace')


def reinterpret_windows1252_as_utf8(wrongtext):
    altered_bytes = []
    for char in wrongtext:
        if ord(char) in WINDOWS_1252_GREMLINS:
            altered_bytes.append(char.encode('WINDOWS_1252'))
        else:
            altered_bytes.append(char.encode('latin-1', 'replace'))
    return b''.join(altered_bytes).decode('utf-8', 'replace')


def reinterpret_latin1_as_macroman(wrongtext):
    "Not used, because it's too risky."
    newbytes = wrongtext.encode('latin1', 'replace')
    return newbytes.decode('macroman', 'replace')


def reinterpret_windows1252_as_macroman(wrongtext):
    "Not used, because it's too risky."
    newbytes = wrongtext.encode('WINDOWS_1252', 'replace')
    return newbytes.decode('macroman', 'replace')


def reinterpret_latin1_as_windows1252(wrongtext):
    """
    Maybe this was always meant to be in a single-byte encoding, and it
    makes the most sense in Windows-1252.
    """
    return wrongtext.encode('latin-1').decode('WINDOWS_1252', 'replace')


def text_cost(text):
    """
    Assign a cost function to the length plus weirdness of a text string.
    """
    return text_badness(text) + len(text) * 4


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


def remove_bom(text):
    """
    Remove a left-over byte-order mark.
    """
    return text.lstrip(unichr(0xfeff))
