# ftfy: fixes text for you

[![PyPI package](https://badge.fury.io/py/ftfy.svg)](https://badge.fury.io/py/ftfy)
[![Docs](https://readthedocs.org/projects/ftfy/badge/?version=latest)](https://ftfy.readthedocs.org/en/latest/)

```python

>>> from ftfy import fix_encoding
>>> print(fix_encoding("(à¸‡'âŒ£')à¸‡"))
(ง'⌣')ง

```

The full documentation of ftfy is available at [ftfy.readthedocs.org](https://ftfy.readthedocs.org). The documentation covers a lot more than this README, so here are some links into it:

- [Fixing problems and getting explanations](https://ftfy.readthedocs.io/en/latest/explain.html)
- [Configuring ftfy](https://ftfy.readthedocs.io/en/latest/config.html)
- [Encodings ftfy can handle](https://ftfy.readthedocs.io/en/latest/encodings.html)
- [“Fixer” functions](https://ftfy.readthedocs.io/en/latest/fixes.html)
- [Is ftfy an encoding detector?](https://ftfy.readthedocs.io/en/latest/detect.html)
- [Heuristics for detecting mojibake](https://ftfy.readthedocs.io/en/latest/heuristic.html)
- [Support for “bad” encodings](https://ftfy.readthedocs.io/en/latest/bad_encodings.html)
- [Command-line usage](https://ftfy.readthedocs.io/en/latest/cli.html)
- [Citing ftfy](https://ftfy.readthedocs.io/en/latest/cite.html)

## Testimonials

- “My life is livable again!”
  — [@planarrowspace](https://twitter.com/planarrowspace)
- “A handy piece of magic”
  — [@simonw](https://twitter.com/simonw)
- “Saved me a large amount of frustrating dev work”
  — [@iancal](https://twitter.com/iancal)
- “ftfy did the right thing right away, with no faffing about. Excellent work, solving a very tricky real-world (whole-world!) problem.”
  — Brennan Young
- “I have no idea when I’m gonna need this, but I’m definitely bookmarking it.”
  — [/u/ocrow](https://reddit.com/u/ocrow)

## What it does

Here are some examples (found in the real world) of what ftfy can do:

ftfy can fix mojibake (encoding mix-ups), by detecting patterns of characters that were clearly meant to be UTF-8 but were decoded as something else:

    >>> import ftfy
    >>> ftfy.fix_text('âœ” No problems')
    '✔ No problems'

Does this sound impossible? It's really not. UTF-8 is a well-designed encoding that makes it obvious when it's being misused, and a string of mojibake usually contains all the information we need to recover the original string.

ftfy can fix multiple layers of mojibake simultaneously:

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

## Installing

ftfy is a Python 3 package that can be installed using `pip`:

    pip install ftfy

(Or use `pip3 install ftfy` on systems where Python 2 and 3 are both globally installed and `pip` refers to Python 2.)

If you use `poetry`, you can use ftfy as a dependency in the usual way (such as `poetry add ftfy`).

### Local development

ftfy is developed using [uv](https://github.com/astral-sh/uv). You can build a virtual environment with its local dependencies by running `uv venv`, and test it with `uv run pytest`.

## Who maintains ftfy?

I'm Robyn Speer, also known as Elia Robyn Lake. You can find my projects
[on GitHub](https://github.com/rspeer) and my posts on [my own blog](https://posts.arborelia.net).

## Citing ftfy

ftfy has been used as a crucial data processing step in major NLP research.

It's important to give credit appropriately to everyone whose work you build on in research. This includes software, not just high-status contributions such as mathematical models. All I ask when you use ftfy for research is that you cite it.

ftfy has a citable record [on Zenodo](https://zenodo.org/record/2591652). A citation of ftfy may look like this:

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

## Important license clarifications

If you do not follow ftfy's license, you do not have a license to ftfy.

This sounds obvious and tautological, but there are people who think open source licenses mean that they can just do what they want, especially in the field of generative AI. It's a permissive license but you still have to follow it. The [Apache license](https://www.apache.org/licenses/LICENSE-2.0) is the only thing that gives you permission to use and copy ftfy; otherwise, all rights are reserved.

If you use or distribute ftfy, you must follow the terms of the [Apache license](https://www.apache.org/licenses/LICENSE-2.0), including that you must attribute the author of ftfy (Robyn Speer) correctly.

You _may not_ make a derived work of ftfy that obscures its authorship, such as by putting its code in an AI training dataset, including the code in AI training at runtime, or using a generative AI that copies code from such a dataset.

At my discretion, I may notify you of a license violation, and give you a chance to either remedy it or delete all copies of ftfy in your possession.

