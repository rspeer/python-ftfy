from ftfy import bad_codecs, guess_bytes


def test_cesu8():
    cls1 = bad_codecs.search_function("cesu8").__class__
    cls2 = bad_codecs.search_function("cesu-8").__class__
    assert cls1 == cls2

    test_bytes = b"\xed\xa6\x9d\xed\xbd\xb7 is an unassigned character, and \xc0\x80 is null"
    test_text = "\U00077777 is an unassigned character, and \x00 is null"
    assert test_bytes.decode("cesu8") == test_text


def test_russian_crash():
    thebytes = b"\xe8\xed\xe2\xe5\xed\xf2\xe0\xf0\xe8\xe7\xe0\xf6\xe8\xff "
    # We don't care what the result is, but this shouldn't crash
    thebytes.decode("utf-8-variants", "replace")

    # This shouldn't crash either
    guess_bytes(thebytes)
