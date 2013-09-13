# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy import bad_codecs
from nose.tools import eq_


def test_cesu8():
    eq_(bad_codecs.search_function('cesu8').__class__, bad_codecs.search_function('cesu-8').__class__)

    test_bytes = b'\xed\xa6\x9d\xed\xbd\xb7 is an unassigned character, and \xc0\x80 is null'
    test_text = '\U00077777 is an unassigned character, and \x00 is null'
    eq_(test_bytes.decode('cesu8'), test_text)