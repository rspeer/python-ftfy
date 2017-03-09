.. ftfy documentation master file, created by
   sphinx-quickstart on Wed Aug 28 03:18:27 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ftfy: fixes text for you
========================

**ftfy** fixes Unicode that's broken in various ways.

The goal of ftfy is to **take in bad Unicode and output good Unicode**, for use
in your Unicode-aware code. This is different from taking in non-Unicode and
outputting Unicode, which is not a goal of ftfy. It also isn't designed to
protect you from having to write Unicode-aware code. ftfy helps those who help
themselves.

Of course you're better off if your input is decoded properly and has no
glitches. But you often don't have any control over your input; it's someone
else's mistake, but it's your problem now.

ftfy will do everything it can to fix the problem.

.. note::

    This documentation is for ftfy 5, which runs on Python 3 only, following
    the plan to drop Python 2 support that was announced in ftfy 3.3.

    If you're running on Python 2, ftfy 4.x will keep working for you. In that
    case, you should add `ftfy < 5` to your requirements.


Mojibake
--------

The most interesting kind of brokenness that ftfy will fix is when someone has
encoded Unicode with one standard and decoded it with a different one.  This
often shows up as characters that turn into nonsense sequences (called
"mojibake"):

- The word ``schön`` might appear as ``schÃ¶n``.
- An em dash (``—``) might appear as ``â€”``.
- Text that was meant to be enclosed in quotation marks might end up
  instead enclosed in ``â€œ`` and ``â€<9d>``, where ``<9d>`` represents an
  unprintable character.

This causes your Unicode-aware code to end up with garbage text because someone
else (or maybe "someone else") made a mistake.

This happens very often to real text. It's often the fault of software that
makes it difficult to use UTF-8 correctly, such as Microsoft Office and some
programming languages. The :func:`ftfy.fix_encoding` function will look for
evidence of mojibake and, when possible, it will undo the process that produced
it to get back the text that was supposed to be there.

Does this sound impossible? It's really not. UTF-8 is a well-designed encoding
that makes it obvious when it's being misused, and a string of mojibake usually
contains all the information we need to recover the original string.

When ftfy is tested on multilingual data from Twitter, it has a false positive
rate of less than 1 per million tweets.


Other fixes
-----------

Any given text string might have other irritating properties, possibly even
interacting with the erroneous decoding. The main function of ftfy,
:func:`ftfy.fix_text`, will fix other problems along the way, such as:

- The text could contain HTML entities such as ``&amp;`` in place of certain
  characters, when you would rather see what the characters actually are.

- For that matter, it could contain instructions for a text terminal to
  do something like change colors, but you are not sending the text to a
  terminal, so those instructions are just going to look like ``^[[30m;``
  or something in the middle of the text.

- The text could write words in non-standard ways for display purposes,
  such as using the three characters ``ﬂ`` ``o`` ``p`` for the word "flop".
  This can happen when you copy text out of a PDF, for example.

- It might not be in *NFC normalized* form. You generally want your text to be
  NFC-normalized, to avoid situations where unequal sequences of codepoints
  can represent exactly the same text. You can also opt for ftfy to use the
  more aggressive *NFKC normalization*.


.. note::

    Before version 4.0, ftfy used NFKC normalization by default. This covered a
    lot of helpful fixes at once, such as expanding ligatures and replacing
    "fullwidth" characters with their standard form. However, it also performed
    transformations that lose information, such as converting `™` to `TM` and
    `H₂O` to `H2O`.

    The default, starting in ftfy 4.0, is to use NFC normalization unless told
    to use NFKC normalization (or no normalization at all). The more helpful
    parts of NFKC are implemented as separate, limited fixes.


There are other interesting things that ftfy can do that aren't part of
the :func:`ftfy.fix_text` pipeline, such as:

* :func:`ftfy.explain_unicode`: show you what's going on in a string,
  for debugging purposes
* :func:`ftfy.fixes.decode_escapes`: do what everyone thinks the built-in
  `unicode_escape` codec does, but this one doesn't *cause* mojibake

Encodings ftfy can handle
-------------------------

ftfy can't fix all possible mix-ups. Its goal is to cover the most common
encoding mix-ups while keeping false positives to a very low rate.

ftfy can understand text that was decoded as any of these single-byte
encodings:

- Latin-1 (ISO-8859-1)
- Windows-1252 (cp1252 -- used in Microsoft products)
- Windows-1251 (cp1251 -- the Russian version of cp1252)
- Windows-1250 (cp1250 -- the Eastern European version of cp1252)
- ISO-8859-2 (which is not quite the same as Windows-1250)
- MacRoman (used on Mac OS 9 and earlier)
- cp437 (used in MS-DOS and some versions of the Windows command prompt)

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

We also can't handle the legacy encodings used for Chinese, Japanese, and
Korean, such as ``shift-jis`` and ``gb18030``.  See `issue #34
<https://github.com/LuminosoInsight/python-ftfy/issues/34>`_ for why this is so
hard.

But remember that the input to ftfy is Unicode, so it handles actual
CJK *text* just fine. It just can't discover that a CJK *encoding* introduced
mojibake into the text.


Using ftfy
----------

The main function, :func:`ftfy.fix_text`, will run text through a sequence of
fixes. If the text changed, it will run them through again, so that you can be
sure the output ends up in a standard form that will be unchanged by
:func:`ftfy.fix_text`.

All the fixes are on by default, but you can pass options to turn them off.
Check that the default fixes are appropriate for your use case. For example:

- You should set `fix_entities` to False if the output is meant to be
  interpreted as HTML.

- You should set `fix_character_width` to False if you want to preserve the
  spacing of CJK text.

- You should set `uncurl_quotes` to False if you want to preserve quotation
  marks with nice typography. You could even consider doing quite the opposite
  of `uncurl_quotes`, running `smartypants`_ on the result to make all the
  punctuation nice.

.. _smartypants: http://pythonhosted.org/smartypants/

If the only fix you need is to detect and repair decoding errors (mojibake), then
you should use :func:`ftfy.fix_encoding` directly.

.. versionchanged:: 4.0
   The default normalization was changed from `'NFKC'` to `'NFC'`. The options
   *fix_latin_ligatures* and *fix_character_width* were added to implement some
   of the less lossy parts of NFKC normalization on top of NFC.

.. autofunction:: ftfy.fix_text

.. autofunction:: ftfy.fix_text_segment

.. autofunction:: ftfy.fix_encoding

.. autofunction:: ftfy.fix_file

.. autofunction:: ftfy.explain_unicode


A note on encoding detection
----------------------------

:func:`ftfy.fix_text` expects its input to be a Python 3 `str` (a Unicode
string).  If you pass in `bytes` instead, ftfy will point you to the `Python
Unicode HOWTO`_.

.. _`Python Unicode HOWTO`: http://docs.python.org/3/howto/unicode.html

Now, you may know that your input is a mess of bytes in an unknown encoding,
and you might want a tool that can just statistically analyze those bytes and
predict what encoding they're in.

ftfy is not that tool. The :func:`ftfy.guess_bytes` function it contains will
do this in very limited cases, but to support more encodings from around the
world, something more is needed.

You may have heard of `chardet`. Chardet is admirable, but it doesn't
completely do the job either. Its heuristics are designed for multi-byte
encodings, such as UTF-8 and the language-specific encodings used in East Asian
languages. It works badly on single-byte encodings, to the point where it will
output wrong answers with high confidence.

:func:`ftfy.guess_bytes` doesn't even try the East Asian encodings, so the
ideal thing would combine the simple heuristic of :func:`ftfy.guess_bytes` with
the multibyte character set detection of `chardet`. This ideal thing doesn't
exist yet.


Accuracy
--------
.. include:: accuracy.rst


Command-line tool
-----------------
ftfy can be used from the command line. By default, it takes UTF-8 input and
writes it to UTF-8 output, fixing problems in its Unicode as it goes.

Here's the usage documentation for the `ftfy` command::

    usage: ftfy [-h] [-o OUTPUT] [-g] [-e ENCODING] [-n NORMALIZATION]
                [--preserve-entities]
                [filename]

    ftfy (fixes text for you), version 5.0

    positional arguments:
      filename              The file whose Unicode is to be fixed. Defaults to -,
                            meaning standard input.

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTPUT, --output OUTPUT
                            The file to output to. Defaults to -, meaning standard
                            output.
      -g, --guess           Ask ftfy to guess the encoding of your input. This is
                            risky. Overrides -e.
      -e ENCODING, --encoding ENCODING
                            The encoding of the input. Defaults to UTF-8.
      -n NORMALIZATION, --normalization NORMALIZATION
                            The normalization of Unicode to apply. Defaults to
                            NFC. Can be "none".
      --preserve-entities   Leave HTML entities as they are. The default is to
                            decode them, as long as no HTML tags have appeared in
                            the file.


Module documentation
====================

*ftfy.fixes*: how individual fixes are implemented
--------------------------------------------------

.. automodule:: ftfy.fixes
   :members: unescape_html, remove_terminal_escapes, uncurl_quotes,
    fix_latin_ligatures, fix_character_width, fix_line_breaks,
    fix_surrogates, remove_control_chars, remove_bom, decode_escapes,
    fix_one_step_and_explain, apply_plan, restore_byte_a0,
    replace_lossy_sequences, fix_partial_utf8_punct_in_1252


*ftfy.badness*: measures the "badness" of text
----------------------------------------------

.. automodule:: ftfy.badness
   :members:


*ftfy.bad_codecs*: support some encodings Python doesn't like
-------------------------------------------------------------

.. automodule:: ftfy.bad_codecs

"Sloppy" encodings
~~~~~~~~~~~~~~~~~~
.. automodule:: ftfy.bad_codecs.sloppy

Variants of UTF-8
~~~~~~~~~~~~~~~~~
.. automodule:: ftfy.bad_codecs.utf8_variants


*ftfy.formatting*: justify Unicode text in a monospaced terminal
----------------------------------------------------------------
.. automodule:: ftfy.formatting
   :members:


*ftfy.chardata* and *ftfy.build_data*: trivia about characters
--------------------------------------------------------------
These files load information about the character properties in Unicode 9.0.
Yes, even if your version of Python doesn't support Unicode 9.0. This ensures
that ftfy's behavior is consistent across versions.

.. automodule:: ftfy.chardata
   :members:

.. autofunction:: ftfy.build_data.make_char_data_file
