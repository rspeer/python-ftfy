from __future__ import unicode_literals
from ftfy import fix_text, fix_text_segment
from nose.tools import eq_


def test_entities():
    example = '&amp;\n<html>\n&amp;'
    eq_(fix_text(example), '&\n<html>\n&amp;')
    eq_(fix_text_segment(example), '&amp;\n<html>\n&amp;')

    eq_(fix_text(example, fix_entities=True), '&\n<html>\n&')
    eq_(fix_text_segment(example, fix_entities=True), '&\n<html>\n&')

    eq_(fix_text(example, fix_entities=False), '&amp;\n<html>\n&amp;')
    eq_(fix_text_segment(example, fix_entities=False), '&amp;\n<html>\n&amp;')

    eq_(fix_text_segment('&lt;&gt;', fix_entities=False), '&lt;&gt;')
    eq_(fix_text_segment('&lt;&gt;', fix_entities=True), '<>')
    eq_(fix_text_segment('&lt;&gt;'), '<>')
    eq_(fix_text_segment('jednocze&sacute;nie'), 'jednocześnie')
    eq_(fix_text_segment('JEDNOCZE&Sacute;NIE'), 'JEDNOCZEŚNIE')
