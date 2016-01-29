# coding: utf-8
from __future__ import unicode_literals
from ftfy import guess_bytes
from ftfy.bad_codecs.utf8_variants import mangle_surrogates, IncrementalDecoder
from nose.tools import eq_
import sys


PYTHON2 = sys.hexversion < 0x03000000

TEST_ENCODINGS = [
    'utf-16', 'utf-8', 'sloppy-windows-1252'
]

TEST_STRINGS = [
    'Renée\nFleming', 'Noël\nCoward', 'Señor\nCardgage',
    '€ • £ • ¥', '¿Qué?'
]


def check_bytes_decoding(string):
    for encoding in TEST_ENCODINGS:
        result_str, result_encoding = guess_bytes(string.encode(encoding))
        eq_(result_str, string)
        eq_(result_encoding, encoding)

    if '\n' in string:
        old_mac_bytes = string.replace('\n', '\r').encode('macroman')
        result_str, result_encoding = guess_bytes(old_mac_bytes)
        eq_(result_str, string.replace('\n', '\r'))


def test_guess_bytes():
    for string in TEST_STRINGS:
        yield check_bytes_decoding, string

    bowdlerized_null = b'null\xc0\x80separated'
    result_str, result_encoding = guess_bytes(bowdlerized_null)
    eq_(result_str, u'null\x00separated')
    eq_(result_encoding, u'utf-8-variants')


def test_mangle_surrogates():
    eq_(b'Eric the half a bee \xed\xa0\x80'.decode('utf-8-variants', 'replace'),
        'Eric the half a bee ���')

    if PYTHON2:
        # These are the encodings of a surrogate character, plus a similar-looking
        # Korean character. Only the surrogate character's bytes should get mangled.
        eq_(mangle_surrogates(b'\xed\xa0\x80\xed\x9e\x99'), b'\xff\xff\xff\xed\x9e\x99')

        # Mangle sequences of surrogates, but don't mangle surrogates later in
        # the string (there's no need to in our decoders).
        eq_(mangle_surrogates(b'\xed\xa0\xbd\xed\xb8\xb9test\xed\xb4\xb4'),
            b'\xff\xff\xff\xff\xff\xfftest\xed\xb4\xb4')
        eq_(mangle_surrogates(b'test\xed\xb4\xb4'), b'test\xed\xb4\xb4')

        # Handle short bytestrings correctly.
        eq_(mangle_surrogates(b'\xed'), b'\xed')
        eq_(mangle_surrogates(b''), b'')
    else:
        # Make sure mangle_surrogates doesn't do anything
        eq_(mangle_surrogates(b'\xed\xa0\x80\xed\x9e\x99'), b'\xed\xa0\x80\xed\x9e\x99')


def test_incomplete_sequences():
    test_bytes = b'surrogates: \xed\xa0\x80\xed\xb0\x80 / null: \xc0\x80'
    test_string = 'surrogates: \U00010000 / null: \x00'

    # Test that we can feed this string to decode() in multiple pieces, and no
    # matter where the break between those pieces is, we get the same result.
    for split_point in range(len(test_string) + 1):
        left = test_bytes[:split_point]
        right = test_bytes[split_point:]

        decoder = IncrementalDecoder()
        got = decoder.decode(left, final=False)
        got += decoder.decode(right)
        eq_(got, test_string)

