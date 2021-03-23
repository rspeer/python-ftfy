ftfy: fixes text for you
========================

**ftfy** fixes Unicode that's broken in various ways.

The goal of ftfy is to **take in bad Unicode and output good Unicode**, for use in your Unicode-aware code.

This is different from taking in non-Unicode and outputting Unicode, which is not a goal of ftfy. It also isn't designed to protect you from having to write Unicode-aware code. ftfy helps those who help themselves.

Of course you're better off if your input is decoded properly and has no glitches. But you often don't have any control over your input; it's someone else's mistake, but it's your problem now.

ftfy will do everything it can to fix the problem.

Some quick examples
-------------------

Here are some examples (found in the real world) of what ftfy can do:

ftfy can fix mojibake (encoding mix-ups), by detecting patterns of characters that were clearly meant to be UTF-8 but were decoded as something else:

    >>> import ftfy
    >>> ftfy.fix_text('âœ” No problems')
    '✔ No problems'

It can fix multiple layers of mojibake simultaneously:

    >>> ftfy.fix_text('The Mona Lisa doesnÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢t have eyebrows.')
    "The Mona Lisa doesn't have eyebrows."

It can fix mojibake that has had "curly quotes" applied on top of it, which cannot be consistently decoded until the quotes are uncurled:

    >>> ftfy.fix_text("l’humanitÃ©")
    "l'humanité"

ftfy can fix mojibake that would have included the character U+A0 (non-breaking space), but the U+A0 was turned into an ASCII space and then combined with another following space:

    >>> ftfy.fix_text('Ã\xa0 perturber la rÃ©flexion')
    'à perturber la réflexion'
    >>> ftfy.fix_text('Ã perturber la rÃ©flexion')
    'à perturber la réflexion'

ftfy can also decode HTML entities that appear outside of HTML, even in cases where the entity has been incorrectly capitalized:

    >>> # by the HTML 5 standard, only 'P&Eacute;REZ' is acceptable
    >>> ftfy.fix_text('P&EACUTE;REZ')
    'PÉREZ'
  
These fixes are not applied in all cases, because ftfy has a strongly-held goal of avoiding false positives -- it should never change correctly-decoded text to something else.

The following text could be encoded in Windows-1252 and decoded in UTF-8, and it would decode as 'MARQUɅ'. However, the original text is already sensible, so it is unchanged.

    >>> ftfy.fix_text('IL Y MARQUÉ…')
    'IL Y MARQUÉ…'

Citing ftfy
-----------
ftfy has been used as a crucial data processing step in major NLP research.

It's important to give credit appropriately to everyone whose work you build on
in research. This includes software, not just high-status contributions such as
mathematical models. All I ask when you use ftfy for research is that you cite
it. 

ftfy has a citable record on `Zenodo`_. A citation of ftfy may look like this:

    Robyn Speer. (2019). ftfy (Version 5.5). Zenodo.
    http://doi.org/10.5281/zenodo.2591652

In BibTeX format, the citation is::

    @misc{speer-2019-ftfy,
      author       = {Robyn Speer},
      title        = {ftfy},
      note         = {Version 5.5},
      year         = 2019,
      howpublished = {Zenodo},
      doi          = {10.5281/zenodo.2591652},
      url          = {https://doi.org/10.5281/zenodo.2591652}
    }

.. _Zenodo: https://zenodo.org/record/2591652

Basic usage
-----------



Individual ways to fix text
===========================

.. automodule:: ftfy.fixes
   :members: unescape_html, remove_terminal_escapes, uncurl_quotes,
    fix_latin_ligatures, fix_character_width, fix_line_breaks,
    fix_surrogates, remove_control_chars, remove_bom, decode_escapes,
    fix_one_step_and_explain, apply_plan, restore_byte_a0,
    replace_lossy_sequences, fix_partial_utf8_punct_in_1252


Is ftfy an encoding detector?
=============================

No. Encoding detectors have ended up being a bad idea, and they are largely responsible for _creating_ the problems that ftfy has to fix.

The text that you put into ftfy should be Unicode that you've attempted to decode correctly. ftfy doesn't accept bytes as input.

There is a lot of Unicode out there that has already been mangled by mojibake, even when decoded properly. That is, you might correctly interpret the text as UTF-8, and what the UTF-8 text really says is a mojibake string like "rÃ©flexion". This is when you need ftfy.


I really need to guess the encoding of some bytes
-------------------------------------------------

I understand. Sometimes we can't have nice things.

Though it's not part of the usual operation of ftfy, ftfy _does_ contain a byte-encoding-guesser that tries to be less terrible than other byte-encoding-guessers: 

.. autofunction:: ftfy.guess_bytes


How can I avoid producing mojibake?
===================================

- **Assume text is in UTF-8** unless you have a specific reason to believe it isn't.

In the 2020s, [UTF-8 is everywhere](http://utf8everywhere.org/), especially in text meant to be transferred over the Internet.

In Python 3, you should use the Unicode string type (`str`) for all operations. You should open text files in UTF-8:

    openfile = open(filename, encoding='utf-8', errors='replace')

When you are specifically working with bytes and you need to turn them into text, you should decode them as UTF-8:

    text = bytebuffer.decode('utf-8', 'replace')

The exceptions, the cases where you're not using UTF-8, are few but relevant. If you're interacting with C APIs, you'll need to represent your text as bytes in the format the API expects. Windows APIs in particular expect UTF-16.

We're mostly past the dark days when encodings were "character maps" of 256 possible characters, one byte per character. An unfortunate thing that keeps them alive is Microsoft Excel, whose "Export" feature will pick a 256-character encoding *based on your computer's operating system and default language*. So:

- **Don't export CSV files from Excel** if you have any other choice.

Excel CSVs aren't even interoperable between different computers. Use Google Sheets to create CSVs, and keep Excel files in Excel format so the Unicode won't be mangled.

If you must export a CSV-like file from Excel, you can find an option to tell Excel to export in "Unicode Text", and it will create a tab-separated UTF-16 file. This is not a very widely-used format, but at least it's not mojibake.

You can follow `these unwieldy directions from a SalesForce help article <https://help.salesforce.com/articleView?id=000324657&type=1&mode=1>` to use Excel and Notepad to create a UTF-8 CSV. You can see why I don't recommend this process.

- **Don't use chardet**.

As described in the previous section, encoding detection is not a good idea. It was important in the '90s, during the rough transition to Unicode -- and it hasn't changed since the '90s. A heuristic designed before there was multilingual social media, before there were emoji, is not going to work correctly in the 2020s.

chardet was built on the assumption that "encoding detection is language detection", which is no longer true. Web sites now contain text in multiple languages, and for the most part they use UTF-8 regardless of the language.

When chardet sees the _correct_ UTF-8 encoding of an emoji, it will have no idea what it's looking at, and will guess that it's Turkish encoded in Windows-1254. On other reasonable text, it will guess the very unpopular "iso-8859-2" encoding. Because the bug is inherent to the design of chardet, it's not easily fixed.


Fixing mojibake and related problems
====================================

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


Citing ftfy
-----------
ftfy has been used as a crucial data processing step in major NLP research.

It's important to give credit appropriately to everyone whose work you build on
in research. This includes software, not just high-status contributions such as
mathematical models. All I ask when you use ftfy for research is that you cite
it. 

ftfy has a citable record on `Zenodo`_. A citation of ftfy may look like this:

    Robyn Speer. (2019). ftfy (Version 5.5). Zenodo.
    http://doi.org/10.5281/zenodo.2591652

In BibTeX format, the citation is::

    @misc{speer-2019-ftfy,
      author       = {Robyn Speer},
      title        = {ftfy},
      note         = {Version 5.5},
      year         = 2019,
      howpublished = {Zenodo},
      doi          = {10.5281/zenodo.2591652},
      url          = {https://doi.org/10.5281/zenodo.2591652}
    }

.. _Zenodo: https://zenodo.org/record/2591652


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
These files load information about the character properties in Unicode 11.0.
Yes, even if your version of Python doesn't support Unicode 11.0. This ensures
that ftfy's behavior is consistent across versions.

.. automodule:: ftfy.chardata
   :members:

.. autofunction:: ftfy.build_data.make_char_data_file
