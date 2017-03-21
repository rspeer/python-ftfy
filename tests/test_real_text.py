"""
Test with text actually found in the wild (mostly on Twitter).

I collected test cases by listening to the Twitter streaming API for
a million or so tweets, picking out examples with high weirdness according
to ftfy version 2, and seeing what ftfy decoded them to. There are some
impressive things that can happen to text, even in an ecosystem that is
supposedly entirely UTF-8.

TEST_CASES contains the most interesting examples of these, often with some
trickiness of how to decode them into the actually intended text.

For some reason, sampling Twitter gives no examples of text being
accidentally decoded as Windows-1250, even though it's one of the more
common encodings and this mojibake has been spotted in the wild. It may be
that Windows-1250 is used in places that culturally don't use Twitter much
(Central and Eastern Europe), and therefore nobody designs a Twitter app or
bot to use Windows-1250. I've collected a couple of examples of
Windows-1250 mojibake from elsewhere.
"""
from ftfy import fix_text
from ftfy.fixes import fix_encoding_and_explain, apply_plan
from nose.tools import eq_
import json
import os


THIS_DIR = os.path.dirname(__file__)
TEST_FILENAME = os.path.join(THIS_DIR, 'test_cases.json')
TEST_DATA = json.load(open(TEST_FILENAME, encoding='utf-8'))


# We set up the tests as a dictionary where they can be looked up by label,
# even though we already have them in a list, so we can call 'check_example' by
# the test label. This will make the test label show up in the name of the test
# in nose.

def _make_tests():
    available_tests = {}
    for val in TEST_DATA:
        label = val['label']
        available_tests[label] = {
            'original': val['original'],
            'fixed': val['fixed'],
            'fixed-encoding': val.get('fixed-encoding', val['fixed'])
        }
    return available_tests


AVAILABLE_TESTS = _make_tests()


def check_example(label):
    # Run the test with the given label in the data file
    val = AVAILABLE_TESTS[label]
    orig = val['original']
    fixed = val['fixed']

    # Make sure that the fix_encoding step outputs a plan that we can
    # successfully run to reproduce its result
    encoding_fix, plan = fix_encoding_and_explain(orig)
    eq_(apply_plan(orig, plan), encoding_fix)

    # Make sure we can decode the text as intended
    eq_(fix_text(orig), fixed)
    eq_(encoding_fix, val['fixed-encoding'])

    # Make sure we can decode as intended even with an extra layer of badness
    extra_bad = orig.encode('utf-8').decode('latin-1')
    eq_(fix_text(extra_bad), fixed)


def test_real_text():
    for test_case in TEST_DATA:
        if test_case['enabled']:
            label = test_case['label']
            yield check_example, label
