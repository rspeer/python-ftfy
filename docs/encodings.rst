Encodings ftfy can handle
=========================

ftfy can't fix all possible mix-ups. Its goal is to cover the most common encoding mix-ups while keeping false positives to a very low rate.

ftfy can understand text that was decoded as any of these single-byte encodings:

- Latin-1 (ISO-8859-1)
- Windows-1252 (cp1252 -- used in Microsoft products)
- Windows-1251 (cp1251 -- the Russian version of cp1252)
- Windows-1250 (cp1250 -- the Eastern European version of cp1252)
- Windows-1253 (cp1253 -- the Greek version of cp1252)
- Windows-1254 (cp1254 -- the Turkish version of cp1252)
- ISO-8859-2 (which is not quite the same as Windows-1250)
- MacRoman (used on Mac OS 9 and earlier)
- cp437 (used in MS-DOS and some versions of the Windows command prompt)

when it was actually intended to be decoded as one of these variable-length encodings:

- UTF-8
- CESU-8 (a common, incorrect implementation of UTF-8)

It can also understand text that was intended as Windows-1252 but decoded as Latin-1. That's the very common case where things like smart-quotes and bullets turn into single weird control characters.

However, ftfy cannot understand other mixups between single-byte encodings, because it is extremely difficult to detect which mixup in particular is the one that happened.

We also can't handle the legacy encodings used for Chinese, Japanese, and Korean, such as ``shift-jis`` and ``gb18030``.  See `issue #34`_ for why this is so hard.

.. _`issue #34`: https://github.com/LuminosoInsight/python-ftfy/issues/34

Remember that the input to ftfy is Unicode, so it handles actual CJK *text* just fine. It just can't discover that a CJK *encoding* introduced mojibake into the text.
