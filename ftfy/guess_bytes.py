import ftfy.bad_codecs
ftfy.bad_codecs.ok()


def guess_bytes(bstring):
    """
    If you have some bytes in an unknown encoding, here's a reasonable
    strategy for decoding them, by trying a few common encodings that
    can be distinguished from each other.

    This is not a magic bullet. If the bytes are coming from some MySQL
    database with the "character set" set to ISO Elbonian, this won't figure
    it out.

    The encodings we try are:

    - UTF-16 with a byte order mark, because a UTF-16 byte order mark looks
      like nothing else
    - UTF-8, because it's the global de facto standard
    - "utf-8-variants", because it's what people actually implement when they
      think they're doing UTF-8
    - MacRoman, because Microsoft Office thinks it's still a thing, and it
      can be distinguished by its line breaks. (If there are no line breaks in
      the string, though, you're out of luck.)
    - "sloppy-windows-1252", the Latin-1-like encoding that is the most common
      single-byte encoding
    """
    if bstring.startswith(b'\xfe\xff') or bstring.startswith(b'\xff\xfe'):
        return bstring.decode('utf-16'), 'utf-16'

    byteset = set(bytes(bstring))
    byte_ed, byte_c0, byte_CR, byte_LF = b'\xed\xc0\r\n'

    try:
        if byte_ed in byteset or byte_c0 in byteset:
            return bstring.decode('utf-8-variants'), 'utf-8-variants'
        else:
            return bstring.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        pass

    if byte_CR in bstring and byte_LF not in bstring:
        return bstring.decode('macroman'), 'macroman'
    else:
        return bstring.decode('sloppy-windows-1252'), 'sloppy-windows-1252'
