## ftfy: fixes text for you

This is a simple module for making text less broken. Works in Python 2.6, 
Python 3.2, or later.

Its main function, `fix_text` aka `ftfy`, performs the following operations on
a Unicode string:

* Detect whether the text was incorrectly encoded into UTF-8 and fix it,
  as defined in `fix_bad_encoding`.
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

If your text is inconsistently encoded, but breaks up into coherent pieces (for
example, line-by-line), then you will be better off feeding the lines into
`fix_text` individually instead of as one huge string.

ftfy will not decode bytes into Unicode for you. You should use Python's
built-in `.decode` for that. If you don't know the encoding, you should use the
`chardet` library.

Author: Rob Speer, rob@lumino.so
