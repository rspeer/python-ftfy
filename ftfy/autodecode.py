from ftfy.chardata import possible_encoding
import codecs
import ftfy.bad_codecs.utf8_variants

def decode_bytes(bstring):
    if bstring.startswith(b'\xfe\xff') or bstring.startswith(b'\xff\xfe'):
        return bstring.decode('utf-16'), 'utf-16'
    
    try:
        return bstring.decode('utf-8'), 'utf-8')
    except UnicodeDecodeError:
        pass

    try:
        return bstring.decode('utf-8-variants'), 'utf-8-variants')
    except UnicodeDecodeError:
        pass

    return bstring.decode('latin-1'), 'latin-1'


