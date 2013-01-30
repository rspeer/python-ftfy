## ftfy: fixes text for you

This is a module for making text less broken. It works in Python 2.6, 
Python 3.2, or later.

Its main function, `fix_text` aka `ftfy`, performs the following operations on
a Unicode string:

* Detect whether the text was incorrectly encoded and fix it, as defined
  in `fix_bad_encoding`.
* If the text is HTML-escaped but has no HTML tags, replace HTML entities
  with their equivalent characters.
* Remove terminal escapes and color codes.
* Remove control characters except for newlines and tabs.
* Normalize it with Unicode normalization form KC, which applies the
  following relevant transformations:
  * Combine characters and diacritics that are written using separate
    code points, such as converting "e" plus an acute accent modifier
    into "é", or converting "ka" (か) plus a dakuten into the
    single character "ga" (が).
  * Replace characters that are functionally equivalent with the most
    common form: for example, half-width katakana will be replaced with
    full-width, full-width Roman characters will be replaced with
    ASCII characters, ellipsis characters will be replaced by three
    periods, and the ligature 'ﬂ' will be replaced by 'fl'.
* Replace curly quotation marks with straight ones.
* Remove an unnecessary byte-order mark (which might come from Microsoft's version
  of UTF-8) from the start.

### Examples

    >>> from __future__ import unicode_literals
    >>> from ftfy import fix_text
    >>> print(fix_text('This â€” should be an em dash'))
    This — should be an em dash

    >>> print(fix_text('uÌˆnicode'))
    ünicode

    >>> wtf = '\xc3\xa0\xc2\xb2\xc2\xa0_\xc3\xa0\xc2\xb2\xc2\xa0'
    >>> print(fix_text(wtf))
    ಠ_ಠ

### Non-Unicode strings

When first using ftfy, you might be confused to find that you can't give it a
bytestring (the type of object called `str` in Python 2).

ftfy fixes text. Treating bytestrings as text is exactly the kind of thing that
causes the Unicode problems that ftfy has to fix. Hypothetically, it might even
be able to let you do such a silly thing, and then fix the problem you just
created. But that creates a cycle of dependence on tools such as ftfy.

So instead of silently fixing your error, ftfy ensures first that *you* are
doing it right -- which means you must give it a Unicode string as input. If
you don't, it'll point you to the
[Python Unicode HOWTO](http://docs.python.org/3/howto/unicode.html).

If you have been given a mess of bytes from somewhere else and you need to handle
them, you can decode those bytes as Latin-1 and let ftfy take it from there.

    >>> print(fix_text(b'\x85test'))
    UnicodeError: [informative error message]

    >>> print(fix_text(b'\x85test'.decode('latin-1')))
    —test

### Encodings supported

`ftfy` will resolve errors that result from mixing up any of the
following encodings:

- UTF-8
- Latin-1
- Windows-1252 (cp1252)

These are the three most commonly-confused encodings, because on English text
they look nearly the same.

(Do you ever encounter files in MacRoman or DOS cp437? I could add support for
detecting and fixing text that has been through one of these encodings, but it
would come with an increased risk of "fixing" other text incorrectly. Open a
bug report on GitHub if you think it would be worthwhile to write the
heuristics to handle these encodings.)

### Command-line usage

ftfy now installs itself as a command line tool, for cleaning up text files
that are a mess of mangled bytes.

You can type `ftfy FILENAME`, and it will read in FILENAME as Latin-1 text, fix
encoding problems (including re-interpreting it as UTF-8 if appropriate), and
write the result to standard out as UTF-8.

Author: Rob Speer, rob@luminoso.com
