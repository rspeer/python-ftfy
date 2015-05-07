# ftfy: fixes text for you

[![Downloads](https://pypip.in/d/ftfy/badge.png)](https://crate.io/packages/ftfy)
[![Version](https://pypip.in/v/ftfy/badge.png)](https://crate.io/packages/ftfy)
[![Docs](https://readthedocs.org/projects/ftfy/badge/?version=latest)](http://ftfy.readthedocs.org/en/latest/)

```python
>>> print(fix_encoding("(à¸‡'Ì€âŒ£'Ì\x81)à¸‡"))
(ง'̀⌣'́)ง
```

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

`ftfy` fixes Unicode that's broken in various ways. It works in Python 2.7,
Python 3.2, or later.

The goal of `ftfy` is to **take in bad Unicode and output good Unicode**, for use
in your Unicode-aware code. This is different from taking in non-Unicode and
outputting Unicode, which is not a goal of ftfy. It also isn't designed to
protect you from having to write Unicode-aware code. ftfy helps those who help
themselves.

Of course you're better off if your input is decoded properly and has no
glitches. But you often don't have any control over your input; it's someone
else's mistake, but it's your problem now.

`ftfy` will do everything it can to fix the problem.

## Mojibake

The most interesting kind of brokenness that ftfy will fix is when someone has
encoded Unicode with one standard and decoded it with a different one.  This
often shows up as characters that turn into nonsense sequences (called
"mojibake"):

- The word ``schön`` might appear as ``schÃ¶n``.
- An em dash (``—``) might appear as ``â€”``.
- Text that was meant to be enclosed in quotation marks might end up
  instead enclosed in ``â€œ`` and ``â€<9d>``, where ``<9d>`` represents an
  unprintable character.

ftfy uses heuristics to detect and undo this kind of mojibake, with a very
low rate of false positives.

## Examples

`fix_text` is the main function of ftfy. This section is meant to give you a
taste of the things it can do. `fix_encoding` is the more specific function
that only fixes mojibake.

Please read [the documentation](http://ftfy.readthedocs.org) for more
information on what ftfy does, and how to configure it for your needs.


```python

>>> print(fix_text('This text should be in â€œquotesâ€\x9d.'))
This text should be in "quotes".

>>> print(fix_text('uÌˆnicode'))
ünicode

>>> print(fix_text('Broken text&hellip; it&#x2019;s ﬂubberiﬁc!',
...                normalization='NFKC'))
Broken text... it's flubberific!

>>> print(fix_text('HTML entities &lt;3'))
HTML entities <3

>>> print(fix_text('<em>HTML entities in HTML &lt;3</em>'))
<em>HTML entities in HTML &lt;3</em>

>>> print(fix_text('\001\033[36;44mI&#x92;m blue, da ba dee da ba '
...               'doo&#133;\033[0m', normalization='NFKC'))
I'm blue, da ba dee da ba doo...

>>> print(fix_text('ＬＯＵＤ　ＮＯＩＳＥＳ'))
LOUD NOISES

>>> print(fix_text('ＬＯＵＤ　ＮＯＩＳＥＳ', fix_character_width=False))
ＬＯＵＤ　ＮＯＩＳＥＳ
```


## Who maintains ftfy?

I'm Rob Speer (rob@luminoso.com).  I develop this tool as part of my
text-understanding company, [Luminoso](http://luminoso.com), where it has
proven essential.

Luminoso provides ftfy as free, open source software under the extremely
permissive MIT license.

You can report bugs regarding ftfy on GitHub and we'll handle them.
