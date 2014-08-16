.. ftfy documentation master file, created by
   sphinx-quickstart on Wed Aug 28 03:18:27 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ftfy: fixes text for you
========================

This is a module for making text less broken and more consistent. It works in
Python 2.7, Python 3.2, or later.

The most interesting kind of brokenness that this resolves is when someone has
encoded Unicode with one standard and decoded it with a different one.  This
often shows up as characters that turn into nonsense sequences (called
"mojibake"):

- The word ``schön`` might appear as ``schÃ¶n``.
- An em dash (``—``) might appear as ``â€”``.
- Text that was meant to be enclosed in quotation marks might end up
  instead enclosed in ``â€œ`` and ``â€`` (and that last character
  probably won't even display as anything meaningful).

This happens very often to real text. Fortunately, the nonsense sequences
usually contain all the information you need to reconstruct what character was
supposed to be there.

Any given text string might have other irritating properties, possibly even
interacting with the erroneous decoding:

- The text could contain HTML entities such as ``&amp;`` in place of certain
  characters, when you would rather see what the characters actually are.
- For that matter, it could contain instructions for a text terminal to
  do something like change colors, but you are not sending the text to a
  terminal, so those instructions are just going to look like ``^[[30m;``
  or something in the middle of the text.
- The text could write words in non-standard ways for display purposes,
  such as using the three characters ``ﬂ`` ``o`` ``p`` for the word "flop".
  This can happen when you copy text out of a PDF, for example.

Of course you're better off if all the text you take as input is decoded
properly and written in standard ways. But often, your input is something you
have no control over. Somebody else's minor mistake becomes your problem.

ftfy will do everything it can to fix the problem.

Encodings ftfy can handle
-------------------------

ftfy can understand text that was decoded as any of these single-byte
encodings:

- Latin-1 (ISO-8859-1)
- Windows-1252 (cp1252 -- used in Microsoft products)
- Windows-1251 (cp1251 -- the Russian version of cp1252)
- MacRoman (used on Mac OS 9 and earlier)
- cp437 (used in MS-DOS)

when it was actually intended to be decoded as one of these variable-length
encodings:

- UTF-8
- CESU-8 (what some people think is UTF-8)

It can also understand text that was intended as Windows-1252 but decoded as
Latin-1. That's the very common case where things like smart-quotes and
bullets turn into single weird control characters.

However, ftfy cannot understand other mixups between single-byte encodings,
because it is extremely difficult to detect which mixup in particular is the
one that happened.

Using ftfy
----------

The main function, `fix_text`, will run text through a sequence of fixes. If
the text changed, it will run them through again, so that you can be sure
the output ends up in a standard form that will be unchanged by `fix_text`.

All the fixes are on by default, but you can pass options to turn them off.

.. autofunction:: ftfy.fix_text

.. autofunction:: ftfy.fix_text_segment

.. autofunction:: ftfy.fix_file

.. autofunction:: ftfy.guess_bytes

.. autofunction:: ftfy.explain_unicode

Non-Unicode strings
-------------------

When first using ftfy, you might be confused to find that you can't give it a
bytestring (the type of object called `str` in Python 2).

ftfy fixes text. Treating bytestrings as text is exactly the kind of thing that
causes the Unicode problems that ftfy has to fix. So if you don't give it a
Unicode string, ftfy will point you to the `Python Unicode HOWTO`_.

.. _`Python Unicode Howto`: http://docs.python.org/3/howto/unicode.html

Reasonable ways that you might exchange data, such as JSON or XML, already have
perfectly good ways of expressing Unicode strings. Given a Unicode string, ftfy
can apply fixes that are very likely to work without false positives.

A note on encoding detection
----------------------------

If your input is a mess of unmarked bytes, you might want a tool that can just
statistically analyze those bytes and predict what encoding they're in.

ftfy is not that tool. The `guess_bytes` function will do this in very limited
cases, but to support more encodings from around the world, something more is
needed.

You may have heard of chardet. Chardet is admirable, but it doesn't completely
do the job either. Its heuristics are designed for multi-byte encodings, such
as UTF-8 and the language-specific encodings used in East Asian languages. It
works badly on single-byte encodings, to the point where it will output wrong
answers with high confidence.

ftfy's `guess_bytes` doesn't even try the East Asian encodings, so the ideal thing
would combine the simple heuristic of `guess_bytes` with the multibyte character
set detection of `chardet`. This ideal thing doesn't exist yet.


Accuracy
--------
.. include:: accuracy.rst

Module documentation
====================

`ftfy.fixes`: how individual fixes are implemented
--------------------------------------------------

.. automodule:: ftfy.fixes
   :members:


`ftfy.bad_codecs`: decode text from encodings Python doesn't like
-----------------------------------------------------------------

.. automodule:: ftfy.bad_codecs
   :members:


`ftfy.badness`: measures the "badness" of text
----------------------------------------------

.. automodule:: ftfy.badness
   :members:


`ftfy.chardata` and `ftfy.build_data`: trivia about characters
--------------------------------------------------------------
These files load information about the character properties in Unicode 6.1.
Yes, even if your version of Python doesn't support Unicode 6.1. This ensures
that ftfy's behavior is consistent across versions.

.. automodule:: ftfy.chardata
   :members:

.. autofunction:: ftfy.build_data.make_char_data_file

