# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.fixes import fix_encoding, fix_encoding_and_explain, apply_plan, possible_encoding, fix_surrogates
from ftfy.badness import sequence_weirdness
import unicodedata
import sys
from nose.tools import eq_

if sys.hexversion >= 0x03000000:
    unichr = chr


# Most single-character strings which have been misencoded should be restored.
def test_bmp_characters():
    for index in range(0xa0, 0xfffd):
        char = unichr(index)
        # Exclude code points that are not assigned
        if unicodedata.category(char) not in ('Co', 'Cn', 'Cs', 'Mc', 'Mn'):
            garble = char.encode('utf-8').decode('latin-1')
            # Exclude characters whose re-encoding is protected by the
            # 'sequence_weirdness' metric
            if sequence_weirdness(garble) >= 0:
                garble2 = char.encode('utf-8').decode('latin-1').encode('utf-8').decode('latin-1')
                for garb in (garble, garble2):
                    fixed, plan = fix_encoding_and_explain(garb)
                    eq_(fixed, char)
                    eq_(apply_plan(garb, plan), char)
            else:
                print("%r <- %r" % (char, garble))


def test_possible_encoding():
    for codept in range(256):
        char = chr(codept)
        assert possible_encoding(char, 'latin-1')


def test_byte_order_mark():
    eq_(fix_encoding('ï»¿'), '\ufeff')


def test_surrogates():
    eq_(fix_surrogates('\udbff\udfff'), '\U0010ffff')
    eq_(fix_surrogates('\ud800\udc00'), '\U00010000')

