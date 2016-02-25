## Version 4.1.0 (February 25, 2016)

Heuristic changes:

- ftfy can now deal with "lossy" mojibake. If your text has been run through
  a strict Windows-1252 decoder, such as the one in Python, it may contain
  the replacement character � (U+FFFD) where there were bytes that are
  unassigned in Windows-1252.

  Although ftfy won't recover the lost information, it can now detect this
  situation, replace the entire lossy character with �, and decode the rest of
  the characters. Previous versions would be unable to fix any string that
  contained U+FFFD.

  As an example, text in curly quotes that gets corrupted `â€œ like this â€�`
  now gets fixed to be `“ like this �`.

- Heuristics now count characters such as `~` and `^` as punctuation instead
  of wacky math symbols, improving the detection of mojibake in some edge cases.

New features:

- A new module, `ftfy.formatting`, can be used to justify Unicode text in a
  monospaced terminal. It takes into account that each character can take up
  anywhere from 0 to 2 character cells.

- Internally, the `utf-8-variants` codec was simplified and optimized.


## Version 4.0.0 (April 10, 2015)

Breaking changes:

- The default normalization form is now NFC, not NFKC. NFKC replaces a large
  number of characters with 'equivalent' characters, and some of these
  replacements are useful, but some are not desirable to do by default.

- The `fix_text` function has some new options that perform more targeted
  operations that are part of NFKC normalization, such as
  `fix_character_width`, without requiring hitting all your text with the huge
  mallet that is NFKC.

  - If you were already using NFC normalization, or in general if you want to
    preserve the *spacing* of CJK text, you should be sure to set
    `fix_character_width=False`.

- The `remove_unsafe_private_use` parameter has been removed entirely, after
  two versions of deprecation. The function name `fix_bad_encoding` is also
  gone.

New features:

- Fixers for strange new forms of mojibake, including particularly clear cases
  of mixed UTF-8 and Windows-1252.

- New heuristics, so that ftfy can fix more stuff, while maintaining
  approximately zero false positives.

- The command-line tool trusts you to know what encoding your *input* is in,
  and assumes UTF-8 by default. You can still tell it to guess with the `-g`
  option.

- The command-line tool can be configured with options, and can be used as a
  pipe.

- Recognizes characters that are new in Unicode 7.0, as well as emoji from
  Unicode 8.0+ that may already be in use on iOS.

Deprecations:

- `fix_text_encoding` is being renamed again, for conciseness and consistency.
  It's now simply called `fix_encoding`. The name `fix_text_encoding` is
  available but emits a warning.

Pending deprecations:

- Python 2.6 support is largely coincidental.

- Python 2.7 support is on notice. If you use Python 2, be sure to pin a
  version of ftfy less than 5.0 in your requirements.


## Version 3.4.0 (January 15, 2015)

New features:

- `ftfy.fixes.fix_surrogates` will fix all 16-bit surrogate codepoints,
  which would otherwise break various encoding and output functions.

Deprecations:

- `remove_unsafe_private_use` emits a warning, and will disappear in the
  next minor or major version.


## Version 3.3.1 (December 12, 2014)

This version restores compatibility with Python 2.6.


## Version 3.3.0 (August 16, 2014)

Heuristic changes:

- Certain symbols are marked as "ending punctuation" that may naturally occur
  after letters. When they follow an accented capital letter and look like
  mojibake, they will not be "fixed" without further evidence.
  An example is that "MARQUÉ…" will become "MARQUÉ...", and not "MARQUɅ".

New features:

- `ftfy.explain_unicode` is a diagnostic function that shows you what's going
  on in a Unicode string. It shows you a table with each code point in
  hexadecimal, its glyph, its name, and its Unicode category.

- `ftfy.fixes.decode_escapes` adds a feature missing from the standard library:
  it lets you decode a Unicode string with backslashed escape sequences in it
  (such as "\u2014") the same way that Python itself would.

- `ftfy.streamtester` is a release of the code that I use to test ftfy on
  an endless stream of real-world data from Twitter. With the new heuristics,
  the false positive rate of ftfy is about 1 per 6 million tweets. (See
  the "Accuracy" section of the documentation.)

Deprecations:

- Python 2.6 is no longer supported.

- `remove_unsafe_private_use` is no longer needed in any current version of
  Python. This fixer will disappear in a later version of ftfy.


## Version 3.2.0 (June 27, 2014)

- `fix_line_breaks` fixes three additional characters that are considered line
  breaks in some environments, such as Javascript, and Python's "codecs"
  library. These are all now replaced with \n:

      U+0085   <control>, with alias "NEXT LINE"
      U+2028   LINE SEPARATOR
      U+2029   PARAGRAPH SEPARATOR


## Version 3.1.3 (May 15, 2014)

- Fix `utf-8-variants` so it never outputs surrogate codepoints, even on
  Python 2 where that would otherwise be possible.


## Version 3.1.2 (January 29, 2014)

- Fix bug in 3.1.1 where strings with backslashes in them could never be fixed


## Version 3.1.1 (January 29, 2014)

- Add the `ftfy.bad_codecs` package, which registers new codecs that can
  decoding things that Python may otherwise refuse to decode:

  - `utf-8-variants`, which decodes CESU-8 and its Java lookalike

  - `sloppy-windows-*`, which decodes character-map encodings while treating
    unmapped characters as Latin-1

- Simplify the code using `ftfy.bad_codecs`.


## Version 3.0.6 (November 5, 2013)

- `fix_entities` can now be True, False, or 'auto'. The new case is True, which
  will decode all entities, even in text that already contains angle brackets.
  This may also be faster, because it doesn't have to check.
- `build_data.py` will refuse to run on Python < 3.3, to prevent building
  an inconsistent data file.


## Version 3.0.5 (November 1, 2013)

- Fix the arguments to `fix_file`, because they were totally wrong.


## Version 3.0.4 (October 1, 2013)

- Restore compatibility with Python 2.6.


## Version 3.0.3 (September 9, 2013)

- Fixed an ugly regular expression bug that prevented ftfy from importing on a
  narrow build of Python.


## Version 3.0.2 (September 4, 2013)

- Fixed some false positives.

  - Basically, 3.0.1 was too eager to treat text as MacRoman or cp437 when
    three consecutive characters coincidentally decoded as UTF-8. Increased the
    cost of those encodings so that they have to successfully decode multiple
    UTF-8 characters.

  - See `tests/test_real_tweets.py` for the new test cases that were added as a
    result.


## Version 3.0.1 (August 30, 2013)

- Fix bug in `fix_java_encoding` that led to only the first instance of
  CESU-8 badness per line being fixed
- Add a fixer that removes unassigned characters that can break Python 3.3
  (http://bugs.python.org/issue18183)


## Version 3.0 (August 26, 2013)

- Generally runs faster
- Idempotent
- Simplified decoding logic
- Understands more encodings and more kinds of mistakes
- Takes options that enable or disable particular normalization steps
- Long line handling: now the time-consuming step (`fix_text_encoding`) will be
  consistently skipped on long lines, but all other fixes will apply
- Tested on millions of examples from Twitter, ensuring a near-zero rate of
  false positives


## Version 2.0.2 (June 20, 2013)

- Fix breaking up of long lines, so it can't go into an infinite loop


## Version 2.0.1 (March 19, 2013)

- Restored Python 2.6 support


## Version 2.0 (January 30, 2013)

- Python 3 support
- Use fast Python built-ins to speed up fixes
- Bugfixes


## Version 1.0 (August 24, 2012)

- Made into its own package with no dependencies, instead of a part of
  `metanl`
