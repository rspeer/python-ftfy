# ftfy test cases

This directory contains JSON files with test cases for ftfy. Many of them are real mojibake found in the wild, such as by listening to the Twitter firehose (when that existed), searching through the OSCAR web crawl, or in issue reports from users.

Cases labeled "synthetic" were not found in the wild, but were instead constructed to test a particular edge case.

Cases labeled "negative" are not mojibake but look lke they could be. We're testing that ftfy does not alter the text (except for its usual processing such as un-curling quotes).

`known-failures.json` contains cases that we would do better at with an improved heuristic. Most of these are false negatives, where ftfy does not figure out how to fix the text. ftfy aims to have no false positives, but there is one synthetic false positive in `known-failures.json`.

## Structure of a test case

A test case contains the following fields:

- `label`: A description of the test case, shown when pytest runs in verbose mode.
- `comment`: Further details on the test case because JSON doesn't have comments.
- `original`: The text to run through ftfy.
- `fixed-encoding` (optional): the expected result of `ftfy.fix_encoding(original)`. If unspecified, uses the value from `fixed`.
- `fixed`: the expected result of `ftfy.fix_text(original)`.
- `expect`: "pass" for test cases that should pass, or "fail" for known failures.