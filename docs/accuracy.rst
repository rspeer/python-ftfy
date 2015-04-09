ftfy uses Twitter's streaming API as an endless source of realistic sample
data. Twitter is massively multilingual, and despite that it's supposed to be
uniformly UTF-8, in practice, any encoding mistake that someone can make will
be made by someone's Twitter client.

This version of ftfy was evaluated on 17,000,000 tweets received from Twitter's
streaming API in April 2015. None of them were false positives.

ftfy changes about 1 in every 8500 tweets. We sampled 1000 of these changes for
further evaluation, and found:

- 980 of them correctly restored the text.
- 12 of them incompletely or incorrectly restored the text, when a sufficiently
  advanced heuristic might have been able to fully recover the text.
- 8 of them represented text that had lost too much information to be fixed.
- None of them changed correct text to incorrect text (these would be false
  positives).

In all the data we've sampled, including from previous versions of ftfy, there
are only two false positives that remain that we know of::

    fix_encoding('├┤a┼┐a┼┐a┼┐a┼┐a') == 'ôaſaſaſaſa'
    fix_encoding('ESSE CARA AI QUEM É¿') == 'ESSE CARA AI QUEM ɿ'
