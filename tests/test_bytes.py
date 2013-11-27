from ftfy.guess_bytes import guess_bytes
from nose.tools import eq_

TEST_ENCODINGS = [
    'utf-16', 'utf-8', 'sloppy-windows-1252'
]

TEST_STRINGS = [
    u'Renée\nFleming', u'Noël\nCoward', u'Señor\nCardgage',
    u'€ • £ • ¥', u'¿Qué?'
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
