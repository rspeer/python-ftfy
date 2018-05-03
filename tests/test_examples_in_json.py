"""
Test ftfy's fixes using the data in `test_cases.json`.

I collected many test cases by listening to the Twitter streaming API for
millions of tweets, picking out examples with high weirdness, and seeing what
ftfy decoded them to. There are some impressive things that can happen to text,
even in an ecosystem that is supposedly entirely UTF-8.

Some examples come from the Common Crawl (particularly those involving
Windows-1250 mojibake, which is more common on arbitrary Web pages than on
Twitter), and some examples marked as 'synthetic' are contrived to test
particular features of ftfy.

Each test case is a dictionary containing the following items:

- "label": a label that will identify the test case in nosetests
- "original": the text to be ftfy'd
- "fixed": what the result of ftfy.fix_text should be on this text

There are also two optional fields:

- "fixed-encoding": what the result of just ftfy.fix_encoding should be.
  If missing, it will be considered to be the same as "fixed".
- "comment": possibly-enlightening commentary on the test case.
"""
from ftfy import fix_text
from ftfy.fixes import fix_encoding_and_explain, apply_plan
import json
import os
import pytest


THIS_DIR = os.path.dirname(__file__)
TEST_FILENAME = os.path.join(THIS_DIR, 'test_cases.json')
TEST_DATA = json.load(open(TEST_FILENAME, encoding='utf-8'))


@pytest.mark.parametrize("test_case", TEST_DATA)
def test_json_example(test_case):
    # Run one example from the data file
    if test_case['enabled']:
        orig = test_case['original']
        fixed = test_case['fixed']

        # Make sure that the fix_encoding step outputs a plan that we can
        # successfully run to reproduce its result
        encoding_fix, plan = fix_encoding_and_explain(orig)
        assert apply_plan(orig, plan) == encoding_fix

        # Make sure we can decode the text as intended
        assert fix_text(orig) == fixed
        assert encoding_fix == test_case.get('fixed-encoding', fixed)

        # Make sure we can decode as intended even with an extra layer of badness
        extra_bad = orig.encode('utf-8').decode('latin-1')
        assert fix_text(extra_bad) == fixed

