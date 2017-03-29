from ftfy import fix_text, fix_text_segment
from ftfy.fixes import unescape_html
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
    eq_(fix_text_segment('ellipsis&#133;', normalization='NFKC'), 'ellipsis...')
    eq_(fix_text_segment('ellipsis&#x85;', normalization='NFKC'), 'ellipsis...')
    eq_(fix_text_segment('broken&#x81;'), 'broken\x81')
    eq_(unescape_html('euro &#x80;'), 'euro €')
    eq_(unescape_html('not an entity &#20x6;'), 'not an entity &#20x6;')
