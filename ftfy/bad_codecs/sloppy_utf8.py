r"""
This file defines a codec called "sloppy-utf-8", which handles two surprisingly
common ways to mangle UTF-8:

- Replace all 0xa0 bytes with 0x20 (because in Windows-1252 it looks like a
  non-breaking space, and that's the same as a space, right?)
- Sprinkle in punctuation from Windows-1252 as single bytes, such as byte 0x85
  for an ellipsis. (The Mac OS Terminal has a similar fix, where 0x85 on its
  own will be displayed as a slightly ugly ellipsis instead of a replacement
  character.)

Aside from these cases, it acts the same as the "utf-8-variants" decoder.
Encoding with "sloppy-utf-8" is the same as encoding with "utf-8".
"""
from __future__ import unicode_literals
import codecs
from ftfy.bad_codecs.utf8_variants import (
    IncrementalEncoder, IncrementalDecoder,
    UTF8IncrementalDecoder
)
NAME = 'sloppy-utf-8'


class SloppyIncrementalDecoder(IncrementalDecoder):
    def _buffer_decode_step(self, input, errors, final):
        """
        There are three possibilities for each decoding step:

        - Decode as much apparently-real UTF-8 as possible.
        - Decode a six-byte CESU-8 sequence at the current position.
        - Decode a Java-style null at the current position.

        When decoding "apparently-real UTF-8", we might get an error,
        and that's where the sloppiness kicks in. If the error is something
        we recognize and can fix, we'll fix it.
        """
        # Get a reference to the superclass method that we'll be using for
        # most of the real work.
        sup = UTF8IncrementalDecoder._buffer_decode

        # Find the next byte position that indicates a variant of UTF-8.
        # CESU-8 sequences always start with 0xed, and Java nulls always
        # start with 0xc0, both of which are conveniently impossible in
        # real UTF-8.
        cutoff1 = input.find(b'\xed')
        cutoff2 = input.find(b'\xc0')

        # Set `cutoff` to whichever cutoff comes first.
        if cutoff1 != -1 and cutoff2 != -1:
            cutoff = min(cutoff1, cutoff2)
        elif cutoff1 != -1:
            cutoff = cutoff1
        elif cutoff2 != -1:
            cutoff = cutoff2
        else:
            # Decode the entire input at once.
            try:
                return sup(input, 'strict', final)
            except UnicodeDecodeError as e:
                return self._handle_errors(input, errors, final, e)

        if cutoff1 == 0:
            # Decode a possible six-byte sequence starting with 0xed.
            return self._buffer_decode_surrogates(sup, input, errors, final)
        elif cutoff2 == 0:
            # Decode a possible two-byte sequence, 0xc0 0x80.
            return self._buffer_decode_null(sup, input, errors, final)
        else:
            # Decode the bytes up until the next weird thing as UTF-8.
            # Set final=True because 0xc0 and 0xed don't make sense in the
            # middle of a sequence, in any variant.
            try:
                return sup(input[:cutoff], 'strict', True)
            except UnicodeDecodeError as e:
                return self._handle_errors(input[:cutoff], errors, final, e)
    
    def _handle_errors(self, input, errors, final, err):
        """
        """
        sup = UTF8IncrementalDecoder._buffer_decode
        
        if err.start > 0:
            return sup(input[:err.start], errors, final)
        else:
            if err.reason == 'invalid start byte':
                byte = input[0:1]

                # We'll be able to do this with a set of integers when we're on Py3 only.
                if byte in b'\x80\x82\x84\x85\x8b\x91\x92\x93\x94\x95\x96\x97\x9b':
                    return byte.decode('windows-1252'), 1
            
            elif err.reason == 'invalid continuation byte':
                cause = input[err.end]
                if cause == ' ':
                    input = input[:err.end] + b'\xa0' + input[err.end + 1:]

            return sup(input, errors, final)


# Everything below here is boilerplate that matches the modules in the
# built-in `encodings` package.
def encode(input, errors='strict'):
    return IncrementalEncoder(errors).encode(input, final=True), len(input)


def decode(input, errors='strict'):
    return SloppyIncrementalDecoder(errors).decode(input, final=True), len(input)


class StreamWriter(codecs.StreamWriter):
    encode = encode


class StreamReader(codecs.StreamReader):
    decode = decode


CODEC_INFO = codecs.CodecInfo(
    name=NAME,
    encode=encode,
    decode=decode,
    incrementalencoder=IncrementalEncoder,
    incrementaldecoder=SloppyIncrementalDecoder,
    streamreader=StreamReader,
    streamwriter=StreamWriter,
)
