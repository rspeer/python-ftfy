.. _heuristic:

Heuristics for detecting mojibake
=================================

The "badness" heuristic
-----------------------

.. automodule:: ftfy.badness
   :members: badness, is_bad


The "UTF-8 detector" heuristic
------------------------------
A more narrow heuristic is defined in ``chardata.py`` as ``UTF8_DETECTOR_RE``. This heuristic looks for specific sequences of mojibake characters that come from the decoding of common UTF-8 sequences.

Text that matches this regular expression can be partially fixed by :func:`ftfy.fixes.decode_inconsistent_utf8`, even when the string as a whole doesn't decode consistently. 

Because of this, the expression requires that the match isn't preceded by likely UTF-8 characters -- if this were allowed, then it might pick two or three characters out of a larger mess of mojibake to decode as another character while leaving the rest untouched. This makes the problem more confusing, doesn't really solve anything, and can even pile up recursively to decode as entirely arbitrary characters.


The "lossy UTF-8"  heuristic
----------------------------
``chardata.py`` also includes ``LOSSY_UTF8_RE``, which is used similarly to the "UTF-8 detector" heuristic. This regular expression matches sequences that look like they were incorrectly decoded from UTF-8, but with characters replaced by question marks or the Unicode replacement character `�`.

Characters that match this heuristic will be replaced by `�` in the :func:`ftfy.fixes.replace_lossy_sequences` fixer.