# ftfy: fixes text for you

This is a module for making text less broken. It works in Python 2.6, 
Python 3.2, or later.

What does it mean for text to be broken?

- The text could have been encoded with one encoding standard, and decoded
  with a different one. The result is that some characters turn into
  nonsense sequences that look like this: `â€”`
- The text could contain HTML entities, but be passed into a system that
  was not designed to read HTML.
- For that matter, it could contain instructions for a text terminal to
  move the cursor or change colors or something, but you are not sending
  the text to a terminal.
- The text could write words in non-standard ways for display purposes,
  such as using the three characters `ﬂ` `o` `p` for the word "flop".
- The text could contain control characters that are designed for a
  certain operating system.

Of course you're better off if all the text you take as input is in the right
format for your application and operating system. But often, your input is
something you have no control over. Somebody else's minor mistake becomes
your problem.

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

- If `remove_terminal_escapes` is True, remove sequences of bytes that are
  instructions for Unix terminals, such as the codes that make text appear
  in different colors.
- If `fix_entities` is True, consider replacing HTML entities with their
  equivalent characters. However, this never applies to text with a pair
  of angle brackets in it already; you're probably not supposed to decode
  entities there, and you'd make things ambiguous if you did.
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
  (It's an instruction to a UTF-16 decoder. It's not meant to actually
  end up in your string.)
- If anything was changed, repeat all the steps, so that the function is
  idempotent. `"&amp;amp;"` will become `"&"`, for example, not `"&amp;"`.

### Encodings ftfy can handle

`ftfy` can understand text that was decoded as any of these single-byte
encodings:

- Latin-1 (ISO-8859-1)
- Windows-1252 (cp1252 -- used in Microsoft products)
- Windows-1251 (cp1251 -- the Russian version of cp1252)
- MacRoman (used on Mac OS 9 and earlier)
- cp437 (used in MS-DOS)

when it was actually intended to be decoded as a variable-length encoding:

- UTF-8
- CESU-8 (what some programmers think is UTF-8)

It can also understand text that was intended as Windows-1252 but decoded as
Latin-1 -- that's when things like smart-quotes and bullets turn into weird
control characters.

### Encodings ftfy can't handle

`ftfy` cannot understand other mixups between single-byte encodings besides
Latin-1 for Windows-1252, because it is extremely difficult to detect which
mixup in particular is the one that happened.

It cannot handle Windows-1250 and ISO-8859-2, and it never will. Look at their
rows on http://en.wikipedia.org/wiki/Polish_code_pages and you might recognize
why there is no hope of ever being able to tell these apart.

## Non-Unicode strings

When first using ftfy, you might be confused to find that you can't give it a
bytestring (the type of object called `str` in Python 2).

ftfy fixes text. Treating bytestrings as text is exactly the kind of thing that
causes the Unicode problems that ftfy has to fix.

So instead of silently fixing your error, ftfy ensures first that *you* are
doing it right -- which means you must give it a Unicode string as input. If
you don't, it'll point you to the
[Python Unicode HOWTO](http://docs.python.org/3/howto/unicode.html).

But what if you all you have is a mess of bytes? Well, you've got a problem,
and ftfy is not quite the right tool to solve it. Maybe you should try getting
your input from a protocol that understands encoding issues, such as JSON or
XML.

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
on single-byte encodings, and outputs wrong answers with high confidence.

There is lots of real-world text that's in an unknown single-byte encoding.
There might be enough information to statistically sort out which encoding is
which. But nothing, so far, actually does that.

## Command-line usage

ftfy installs itself as a command line tool, for cleaning up text files that
are a mess of mangled bytes.

You can type `ftfy FILENAME`, and it will read in FILENAME as Latin-1 text, fix
everything that `fix_text` fixes (including re-interpreting it as UTF-8 if
appropriate), and write the result to standard out as UTF-8.

This is not necessarily a good idea, but it's kind of convenient. Consider this
a proof of concept until we get a real encoding detector.

## Who's behind this tool?

I'm Rob Speer (rob@luminoso.com).  I develop this tool as part of my
text-understanding company, [Luminoso](http://luminoso.com), where it has
proven essential.

Luminoso provides ftfy as free, open source software under the extremely
permissive MIT license.

You can report bugs regarding ftfy on GitHub and we'll handle them.
