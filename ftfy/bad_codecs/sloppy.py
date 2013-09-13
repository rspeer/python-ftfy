from __future__ import unicode_literals
import codecs
from encodings import normalize_encoding
from ftfy.compatibility import unichr

REPLACEMENT_CHAR = '\ufffd'

def make_sloppy_codec(encoding):
    decoding_list = []
    for byte in range(0x100):
        char = unichr(byte).encode('latin-1').decode(encoding, errors='replace')
        if char == REPLACEMENT_CHAR:
            char = unichr(byte)
        decoding_list.append(char)
    decoding_table = ''.join(decoding_list)
    encoding_table = codecs.charmap_build(decoding_table)

    class Codec(codecs.Codec):
        def encode(self,input,errors='strict'):
            return codecs.charmap_encode(input,errors,encoding_table)

        def decode(self,input,errors='strict'):
            return codecs.charmap_decode(input,errors,decoding_table)

    class IncrementalEncoder(codecs.IncrementalEncoder):
        def encode(self, input, final=False):
            return codecs.charmap_encode(input,self.errors,encoding_table)[0]

    class IncrementalDecoder(codecs.IncrementalDecoder):
        def decode(self, input, final=False):
            return codecs.charmap_decode(input,self.errors,decoding_table)[0]

    class StreamWriter(Codec,codecs.StreamWriter):
        pass

    class StreamReader(Codec,codecs.StreamReader):
        pass

    return codecs.CodecInfo(
        name='cp1252',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )

CODECS = {}
INCOMPLETE_ENCODINGS = (
    ['windows-%s' % num for num in range(1250, 1259)] +
    ['iso-8859-%s' % num for num in (3, 6, 7, 8, 11)]
)

for _encoding in INCOMPLETE_ENCODINGS:
    _new_name = normalize_encoding('sloppy-' + _encoding)
    CODECS[_new_name] = make_sloppy_codec(_encoding)

