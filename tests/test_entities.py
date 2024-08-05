import pytest

from ftfy import fix_text, fix_text_segment
from ftfy.fixes import unescape_html


def test_entities():
    example = "&amp;\n<html>\n&amp;"
    assert fix_text(example) == "&\n<html>\n&amp;"
    assert fix_text_segment(example) == "&amp;\n<html>\n&amp;"

    assert fix_text(example, unescape_html=True) == "&\n<html>\n&"
    assert fix_text_segment(example, unescape_html=True) == "&\n<html>\n&"

    assert fix_text(example, unescape_html=False) == "&amp;\n<html>\n&amp;"
    assert fix_text_segment(example, unescape_html=False) == "&amp;\n<html>\n&amp;"

    assert fix_text_segment("&lt;&gt;", unescape_html=False) == "&lt;&gt;"
    assert fix_text_segment("&lt;&gt;", unescape_html=True) == "<>"
    assert fix_text_segment("&lt;&gt;") == "<>"
    assert fix_text_segment("jednocze&sacute;nie") == "jednocześnie"
    assert fix_text_segment("JEDNOCZE&Sacute;NIE") == "JEDNOCZEŚNIE"
    assert fix_text_segment("ellipsis&#133;", normalization="NFKC") == "ellipsis..."
    assert fix_text_segment("ellipsis&#x85;", normalization="NFKC") == "ellipsis..."
    assert fix_text_segment("broken&#x81;") == "broken\x81"
    assert fix_text_segment("&amp;amp;amp;") == "&"
    assert unescape_html("euro &#x80;") == "euro €"
    assert unescape_html("EURO &EURO;") == "EURO €"
    assert unescape_html("not an entity &#20x6;") == "not an entity &#20x6;"
    assert unescape_html("JEDNOCZE&SACUTE;NIE") == "JEDNOCZEŚNIE"
    assert unescape_html("V&SCARON;ICHNI") == "VŠICHNI"
    assert unescape_html("&#xffff;") == ""
    assert unescape_html("&#xffffffff;") == "\ufffd"
    assert (
        fix_text_segment("this is just informal english &not html")
        == "this is just informal english &not html"
    )


def test_old_parameter_name():
    example = "&amp;\n<html>\n&amp;"
    with pytest.deprecated_call():
        assert fix_text(example, fix_entities=True) == "&\n<html>\n&"
    with pytest.deprecated_call():
        assert fix_text(example, fix_entities=False) == "&amp;\n<html>\n&amp;"
