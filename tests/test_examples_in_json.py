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

import json
import os

import pytest

from ftfy import apply_plan, fix_and_explain, fix_encoding_and_explain, fix_text

THIS_DIR = os.path.dirname(__file__)
TEST_FILENAME = os.path.join(THIS_DIR, "test_cases.json")
TEST_DATA = json.load(open(TEST_FILENAME, encoding="utf-8"))

TESTS_THAT_PASS = [test for test in TEST_DATA if test["expect"] == "pass"]
TESTS_THAT_FAIL = [test for test in TEST_DATA if test["expect"] == "fail"]


@pytest.mark.parametrize("test_case", TEST_DATA)
def test_well_formed_example(test_case):
    assert test_case["expect"] in ("pass", "fail")


@pytest.mark.parametrize("test_case", TESTS_THAT_PASS)
def test_json_example(test_case):
    # Run one example from the data file
    orig = test_case["original"]
    fixed = test_case["fixed"]

    # Make sure that we can fix the text as intended
    assert fix_text(orig) == fixed

    # Make sure that fix_and_explain outputs a plan that we can successfully
    # run to reproduce its result
    fixed_output, plan = fix_and_explain(orig)
    assert apply_plan(orig, plan) == fixed_output

    # Do the same for fix_encoding_and_explain
    encoding_fix, plan = fix_encoding_and_explain(orig)
    assert apply_plan(orig, plan) == encoding_fix

    # Ask for the encoding fix a different way, by disabling all the other steps
    # in the config object
    assert (
        fix_text(
            orig,
            unescape_html=False,
            remove_terminal_escapes=False,
            fix_character_width=False,
            fix_latin_ligatures=False,
            uncurl_quotes=False,
            fix_line_breaks=False,
            fix_surrogates=False,
            remove_control_chars=False,
            normalization=None,
        )
        == encoding_fix
    )

    # Make sure we can decode the text as intended
    assert fix_text(orig) == fixed
    assert encoding_fix == test_case.get("fixed-encoding", fixed)

    # Make sure we can decode as intended even with an extra layer of badness
    extra_bad = orig.encode("utf-8").decode("latin-1")
    assert fix_text(extra_bad) == fixed


@pytest.mark.parametrize("test_case", TESTS_THAT_FAIL)
@pytest.mark.xfail(strict=True)
def test_failing_json_example(test_case):
    # Run an example from the data file that we believe will fail, due to
    # ftfy's heuristic being insufficient
    orig = test_case["original"]
    fixed = test_case["fixed"]

    encoding_fix, plan = fix_encoding_and_explain(orig)
    assert encoding_fix == test_case.get("fixed-encoding", fixed)
