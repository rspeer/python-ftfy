# ftfy: fixes text for you

[![Downloads](https://pypip.in/d/ftfy/badge.png)](https://crate.io/packages/ftfy)
[![Version](https://pypip.in/v/ftfy/badge.png)](https://crate.io/packages/ftfy)
[![Docs](https://readthedocs.org/projects/ftfy/badge/?version=latest)](http://ftfy.readthedocs.org/en/latest/)

Full documentation: **http://ftfy.readthedocs.org**

## Testimonials

- “My life is livable again!”
  — [@planarrowspace](http://twitter.com/planarrowspace)
- “A handy piece of magic”
  — [@simonw](http://twitter.com/simonw)
- “Hat mir die Tage geholfen. Im Übrigen bin ich der Meinung, dass wir keine komplexen Maschinen mit Computern bauen sollten solange wir nicht einmal Umlaute sicher verarbeiten können. :D”
  — [Bruno Ranieri](http://yrrsinn.de/2012/09/17/gelesen-kw37/)
- “I have no idea when I’m gonna need this, but I’m definitely bookmarking it.”
  — [/u/ocrow](http://reddit.com/u/ocrow)
- “9.2/10”
  — [pylint](https://bitbucket.org/logilab/pylint/)

## Developed at Luminoso

[Luminoso](http://www.luminoso.com) makes groundbreaking software for text
analytics that really understands what words mean, in many languages. Our
software is used by enterprise customers such as Sony, Intel, Mars, and Scotts,
and it's built on Python and open-source technologies.

We use ftfy every day at Luminoso, because the first step in understanding text
is making sure it has the correct characters in it!

Luminoso is growing fast and hiring in all areas. If you're interested in
joining us, take a look at [our careers
page](http://www.luminoso.com/career.html).

## What it does

ftfy makes Unicode text less broken and more consistent. It works in
Python 2.7, Python 3.2, or later.

The most interesting kind of brokenness that this resolves is when someone
has encoded Unicode with one standard and decoded it with a different one.
This often shows up as characters that turn into nonsense sequences:

- The word `schön` might appear as `schÃ¶n`.
- An em dash (`—`) might appear as `â€”`.
- Text that was meant to be enclosed in quotation marks might end up
  instead enclosed in `â€œ` and `â€<9d>` (where `<9d>` is an unprintable
  codepoint).

This is called "mojibake", and it happens very often to real text. Fortunately,
the nonsense sequences usually contain all the information you need to
reconstruct what character was supposed to be there.

Any given text string might have other irritating properties, possibly even
interacting with the erroneous decoding:

- The text could contain HTML entities such as `&amp;` in place of certain
  characters, when you would rather see what the characters actually are.
- For that matter, it could contain instructions for a text terminal to
  do something like change colors, but you are not sending the text to a
  terminal, so those instructions are just going to look like `^[[30m;`
  or something in the middle of the text.
- The text could write words in non-standard ways for display purposes,
  such as using the three characters `ﬂ` `o` `p` for the word "flop".
  This can happen when you copy text out of a PDF, for example.

Of course you're better off if all the text you take as input is decoded
properly and written in standard ways. But often, your input is something you
have no control over. Somebody else's minor mistake becomes your problem.

ftfy will do everything it can to fix the problem.

## Examples

In these examples, `unicode_literals` are turned on. ftfy always expects
Unicode strings as input. 

    >>> from __future__ import unicode_literals
    >>> from ftfy import fix_text

    >>> print(fix_text('This â€” should be an em dash'))
    This — should be an em dash

    >>> print(fix_text('uÌˆnicode'))
    ünicode

    >>> print(fix_text('Broken text&hellip; it&#x2019;s ﬂubberiﬁc!'))
    Broken text... it's flubberific!

    >>> print(fix_text('HTML entities &lt;3'))
    HTML entities <3

If any HTML tags appear in your input, ftfy will make sure to leave the HTML
entities alone:

    >>> print(fix_text('<em>HTML entities &lt;3</em>'))
    <em>HTML entities &lt;3</em>

ftfy repeats its process until it reaches a result that it won't change:

    >>> wtf = '\xc3\xa0\xc2\xb2\xc2\xa0_\xc3\xa0\xc2\xb2\xc2\xa0'
    >>> print(fix_text(wtf))
    ಠ_ಠ

## Using ftfy

The main function, `fix_text`, will run text through a sequence of fixes. If
the text changed, it will run them through again, so that you can be sure
the output ends up in a standard form that will be unchanged by `fix_text`.

All the fixes are on by default, but you can pass options to turn them off.
    
- If `fix_entities` is True, replace HTML entities with their equivalent
  characters. If it's "auto" (the default), then consider replacing HTML
  entities, but don't do so in text where you have seen a pair of actual
  angle brackets (that's probably actually HTML and you shouldn't mess
  with the entities).
- If `remove_terminal_escapes` is True, remove sequences of bytes that are
  instructions for Unix terminals, such as the codes that make text appear
  in different colors.
- If `fix_encoding` is True, look for common mistakes that come from
  encoding or decoding Unicode text incorrectly, and fix them if they are
  reasonably fixable. See `fix_text_encoding` for details.
- If `normalization` is not None, apply the specified form of Unicode
  normalization, which can be one of 'NFC', 'NFKC', 'NFD', and 'NFKD'.
  The default, 'NFKC', applies the following relevant transformations:

  - C: Combine characters and diacritics that are written using separate
    code points, such as converting "e" plus an acute accent modifier
    into "é", or converting "ka" (か) plus a dakuten into the
    single character "ga" (が).
  - K: Replace characters that are functionally equivalent with the most
    common form. For example, half-width katakana will be replaced with
    full-width versions, full-width Roman characters will be replaced with
    ASCII characters, ellipsis characters will be replaced with three
    periods, and the ligature 'ﬂ' will be replaced with 'fl'.

- If `uncurl_quotes` is True, replace various curly quotation marks with
  plain-ASCII straight quotes.
- If `fix_line_breaks` is true, convert all line breaks to Unix style
  (CRLF and CR line breaks become LF line breaks).
- If `fix_control_characters` is true, remove all C0 control characters
  except the common useful ones: TAB, CR, LF, and FF. (CR characters
  may have already been removed by the `fix_line_breaks` step.)
- If `remove_bom` is True, remove the Byte-Order Mark if it exists.
- If anything was changed, repeat all the steps, so that the function is
  idempotent. "&amp;amp;amp;" will become "&", for example, not "&amp;amp;".


### Encodings ftfy can handle

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

## Non-Unicode strings

When first using ftfy, you might be confused to find that you can't give it a
bytestring (the type of object called `str` in Python 2).

ftfy fixes text. Treating bytestrings as text is exactly the kind of thing that
causes the Unicode problems that ftfy has to fix. So if you don't give it a
Unicode string, ftfy will point you to the [Python Unicode
HOWTO](http://docs.python.org/3/howto/unicode.html).

Reasonable ways that you might exchange data, such as JSON or XML, already have
perfectly good ways of expressing Unicode strings. Given a Unicode string, ftfy
can apply fixes that are very likely to work without false positives.

### A note on encoding detection

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

## Command-line usage

ftfy installs itself as a command line tool that reads a file and applies
`fix_text` to it.

This has exactly the problem described above: a file on a disk is made of bytes
in an unspecified encoding. It has to guess the encoding of the bytes in the
file. But if it guesses wrong, it might be able to fix it anyway, because
that's what ftfy does.

You can type `ftfy FILENAME`, and it will read in FILENAME, guess its encoding,
fix everything that `fix_text` fixes, and write the result to standard out as
UTF-8.

## Who maintains ftfy?

I'm Robyn Speer (rspeer@luminoso.com).  I develop this tool as part of my
text-understanding company, [Luminoso](http://luminoso.com), where it has
proven essential.

Luminoso provides ftfy as free, open source software under the extremely
permissive MIT license.

You can report bugs regarding ftfy on GitHub and we'll handle them.

## More details

To learn how the pieces of ftfy work:

- You could just read the code. I recommend it. There are copious comments and
  everything has a docstring.
- You can read nicely-formatted documentation at http://ftfy.readthedocs.org.
