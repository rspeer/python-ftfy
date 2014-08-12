This version of ftfy was evaluated on 12,200,000 tweets received from Twitter's streaming API, in early 2014.

1627 (0.013%) of them were detected by ftfy as containing mojibake. These tweets fall into three categories:

- True positives: ftfy turns incorrect text into correct text.
- False positives: ftfy turns correct text into incorrect text.
- Confusions: ftfy turns incorrect text into different incorrect text.

The results for the 1627 tweets that ftfy found were:

- True positives: 1587 (97.54%)
- False positives: 2 (0.12%)
- Confusions: 38 (2.34%)

Two false positives in 12,200,000 examples corresponds to an overall false positive rate of 0.16 per million.
