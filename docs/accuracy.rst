ftfy uses Twitter's streaming API as an endless source of realistic sample
data. Twitter is massively multilingual, and despite that it's supposed to be
uniformly UTF-8, in practice, any encoding mistake that someone can make will
be made by someone's Twitter client.

We check what ftfy's :func:`fix_encoding` heuristic does to this data, and we
aim to have the rate of false positives be indistinguishable from zero.

A pre-release version of ftfy was evaluated on 30,880,000 tweets received from
Twitter's streaming API in April 2015. There was 1 false positive, and it was
due to a bug that has now been fixed.

When looking at the changes ftfy makes, we found:

- :func:`ftfy.fix_text`, with all default options, will change about 1 in 18 tweets.
- With stylistic changes (`fix_character_width` and `uncurl_quotes`) turned off,
  :func:`ftfy.fix_text` will change about 1 in every 300 tweets.
- :func:`ftfy.fix_encoding` alone will change about 1 in every 8500 tweets.

We sampled 1000 of these :func:`ftfy.fix_encoding` changes for further
evaluation, and found:

- 980 of them correctly restored the text.
- 12 of them incompletely or incorrectly restored the text, when a sufficiently
  advanced heuristic might have been able to fully recover the text.
- 8 of them represented text that had lost too much information to be fixed.
- None of those 1000 changed correct text to incorrect text (these would be
  false positives).

In all the data we've sampled, including from previous versions of ftfy, there
are only three false positives that remain that we know of::

    fix_encoding('├┤a┼┐a┼┐a┼┐a┼┐a') == 'ôaſaſaſaſa'
    fix_encoding('ESSE CARA AI QUEM É¿') == 'ESSE CARA AI QUEM ɿ'
    fix_encoding('``hogwarts nao existe, voce nao vai pegar o trem pra lá´´')
      == '``hogwarts nao existe, voce nao vai pegar o trem pra lᴴ'


