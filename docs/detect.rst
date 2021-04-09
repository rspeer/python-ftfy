Is ftfy an encoding detector?
=============================

No, it's a mojibake detector (and fixer). That makes its task much easier, because it doesn't have to guess the encoding of everything: it can leave correct-looking text as it is.

Encoding detectors have ended up being a bad idea, and they are largely responsible for *creating* the problems that ftfy has to fix.

The text that you put into ftfy should be Unicode that you've attempted to decode correctly. ftfy doesn't accept bytes as input.

There is a lot of Unicode out there that has already been mangled by mojibake, even when decoded properly. That is, you might correctly interpret the text as UTF-8, and what the UTF-8 text really says is a mojibake string like "rÃ©flexion" that needs to be decoded *again*. This is when you need ftfy.


I really need to guess the encoding of some bytes
-------------------------------------------------

I understand. Sometimes we can't have nice things.

Though it's not part of the usual operation of ftfy, ftfy *does* contain a byte-encoding-guesser that tries to be less terrible than other byte-encoding-guessers in common cases. Instead of using probabilistic heuristics, it picks up on very strong signals like "having a UTF-16 byte-order mark" or "decoding successfully as UTF-8".

This function won't solve everything. It can't solve everything. In particular, it has no capacity to guess non-Unicode CJK encodings such as Shift-JIS or Big5.

.. autofunction:: ftfy.guess_bytes

