# ftfy: fixes text for you

[![Downloads](https://pypip.in/d/ftfy/badge.png)](https://crate.io/packages/ftfy)
[![Version](https://pypip.in/v/ftfy/badge.png)](https://crate.io/packages/ftfy)

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
- “Too many branches”
  — [pylint](https://bitbucket.org/logilab/pylint/)

## What it does

ftfy makes Unicode text less broken and more consistent. It works in
Python 2.6, Python 3.2, or later.

The most interesting kind of brokenness that this resolves is when someone
has encoded Unicode with one standard and decoded it with a different one.
This often shows up as characters that turn into nonsense sequences:

- The word `schön` might appear as `schÃ¶n`.
- An em dash (`—`) might appear as `â€”`.
- Text that was meant to be enclosed in quotation marks might end up
  instead enclosed in `â€œ` and `â€` (and that last character
  probably won't even display as anything meaningful).

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

    >>> print(fix_text('<em>HTML entities &lt;3</em>'))
    <em>HTML entities &lt;3</em>

    >>> wtf = '\xc3\xa0\xc2\xb2\xc2\xa0_\xc3\xa0\xc2\xb2\xc2\xa0'
    >>> print(fix_text(wtf))
    ಠ_ಠ

## Using ftfy

The main function, `fix_text`, will run text through a sequence of fixes. If
the text changed, it will run them through again, so that you can be sure
the output ends up in a standard form that will be unchanged by `fix_text`.

All the fixes are on by default, but you can pass options to turn them off.

- If `remove_unsafe_private_use` is True, remove a range of unassigned
  characters that can crash Python via
  [bug 18183](http://bugs.python.org/issue18183). This fix will turn itself
  off when you're using Python 3.4 or better, which you probably aren't.
- If `fix_entities` is True, consider replacing HTML entities with their
  equivalent characters. However, this never applies to text with a pair
  of angle brackets in it already; you're probably not supposed to decode
  entities there, and you'd make things ambiguous if you did.
- If `remove_terminal_escapes` is True, remove sequences of bytes that are
  instructions for Unix terminals, such as the codes that make text appear
  in different colors.
- If `fix_encoding` is True, look for common mistakes that come from
  encoding or decoding Unicode text incorrectly, and fix them if they are
  reasonably fixable.
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
  (It's a hint for a UTF-16 decoder. It's not meant to actually
  end up in your string.)
- If anything was changed, repeat all the steps, so that the function is
  idempotent. `"&amp;amp;"` will become `"&"`, for example, not `"&amp;"`.

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

But what if you all you actually have is a mess of bytes on a disk? Well,
you've got a problem, and ftfy is not quite the right tool to solve it.

As a sort of half-measure that covers a few common cases, you can decode the
bytes as Latin-1 and let ftfy take it from there, which might include
reinterpreting the Latin-1 text as Windows-1252 or UTF-8.

    >>> print(fix_text(b'\x85test'))
    UnicodeError: [informative error message]

    >>> print(fix_text(b'\x85test'.decode('latin-1')))
    —test

### A note on encoding detection

If your input is a mess of unmarked bytes, you might want a tool that can just
statistically analyze those bytes and predict what encoding they're in.

ftfy is not that tool. I might want to write that tool someday.

You may have heard of chardet. Chardet is admirable, but it is not that tool
either. Its heuristics only work on multi-byte encodings, such as UTF-8 and the
language-specific encodings used in East Asian languages. It works very badly
on single-byte encodings, to the point where it will output wrong answers with
high confidence.

There is lots of real-world text that's in an unknown single-byte encoding.
There might be enough information to statistically sort out which encoding is
which. But nothing, so far, actually does that.

## Command-line usage

ftfy installs itself as a command line tool that reads a file and applies
`fix_text` to it.

This has exactly the problem described above: a file on a disk is made of bytes
in an unspecified encoding. It could assume the file is UTF-8, but if you had
totally valid UTF-8 you probably wouldn't need this command line utility, and
there's a slight chance that the file could contain Latin-1 that coincidentally
looks like UTF-8.

Instead, it will follow the "half-measure" above.

You can type `ftfy FILENAME`, and it will read in FILENAME as Latin-1 text, fix
everything that `fix_text` fixes (including re-interpreting it as UTF-8 if
appropriate), and write the result to standard out as UTF-8.

This is not necessarily a good idea, but it's convenient. Consider this a proof
of concept until we get a real encoding detector.

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
