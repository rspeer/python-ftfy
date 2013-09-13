import codecs
from encodings import normalize_encoding

_cache = {}

# Define some aliases for 'utf-8-variants'
UTF8_VAR_NAMES = (
    'utf_8_variants', 'utf8_variants',
    'utf_8_variant', 'utf8_variant',
    'utf_8_var', 'utf8_var',
    'cesu_8', 'cesu8',
    'java_utf_8', 'java_utf8'
)


def search_function(encoding):
    if encoding in _cache:
        return _cache[encoding]

    norm_encoding = normalize_encoding(encoding)
    codec = None
    if norm_encoding in UTF8_VAR_NAMES:
        from ftfy.bad_codecs.utf8_variants import CODEC_INFO
        codec = CODEC_INFO
    elif norm_encoding.startswith('sloppy_'):
        from ftfy.bad_codecs.sloppy import CODECS
        return CODECS.get(norm_encoding)

    if codec is not None:
        _cache[encoding] = codec

    return codec


codecs.register(search_function)
