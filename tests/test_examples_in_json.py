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
from nose.tools import eq_
import json
import os


THIS_DIR = os.path.dirname(__file__)
TEST_FILENAME = os.path.join(THIS_DIR, 'test_cases.json')
TEST_DATA = json.load(open(TEST_FILENAME, encoding='utf-8'))


def check_example(val):
    # Run one example from the data file
    orig = val['original']
    fixed = val['fixed']

    # Make sure that the fix_encoding step outputs a plan that we can
    # successfully run to reproduce its result
    encoding_fix, plan = fix_encoding_and_explain(orig)
    eq_(apply_plan(orig, plan), encoding_fix)

    # Make sure we can decode the text as intended
    eq_(fix_text(orig), fixed)
    eq_(encoding_fix, val.get('fixed-encoding', fixed))

    # Make sure we can decode as intended even with an extra layer of badness
    extra_bad = orig.encode('utf-8').decode('latin-1')
    eq_(fix_text(extra_bad), fixed)


def test_cases():
    # Run all the test cases in `test_cases.json`
    for test_case in TEST_DATA:
        if test_case['enabled']:
            desc = "test_examples_in_json.check_example({!r})".format(
                test_case['label']
            )
            check_example.description = desc
            yield check_example, test_case
