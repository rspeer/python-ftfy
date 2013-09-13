r"""
This file defines a codec called "utf-8-variants" (or "utf-8-var"), which can
decode text that's been encoded with a popular non-standard version of UTF-8.
This includes CESU-8, the accidental encoding made by layering UTF-8 on top of
UTF-16, as well as Java's twist on CESU-8 that contains a two-byte encoding for
codepoint 0.

This is particularly relevant in Python 3, which provides no other way of
decoding CESU-8 or Java's encoding. [1]

The easiest way to use the codec is simply to import `ftfy.bad_codecs`:

    >>> import ftfy.bad_codecs
    >>> b'here comes a null! \xc0\x80'.decode('utf-8-var')
    'here comes a null! \x00'

The codec does not at all enforce "correct" CESU-8. For example, the Unicode
Consortium's not-quite-standard describing CESU-8 requires that there is only
one possible encoding of any character, so it does not allow mixing of valid
UTF-8 and CESU-8. This codec *does* allow that, just like Python 2's UTF-8
decoder does.

Characters in the Basic Multilingual Plane still have only one encoding. This
codec still enforces the rule, within the BMP, that characters must appear in
their shortest form. There is one exception: the sequence of bytes `0xc0 0x80`,
instead of just `0x00`, may be used to encode the null character `U+0000`, like
in Java.

If you encode with this codec, you get legitimate UTF-8. Decoding with this
codec and then re-encoding is not idempotent, although encoding and then
decoding is. So this module won't produce CESU-8 for you. Look for that
functionality in the sister module, "Broke That For You", coming approximately
never.

[1] In a pinch, you can decode CESU-8 in Python 2 using the UTF-8 codec: first
decode the bytes (incorrectly), then encode them, then decode them again.
"""

from __future__ import unicode_literals
from ftfy.compatibility import bytes_to_ints, unichr
from encodings.utf_8 import (IncrementalDecoder as UTF8IncrementalDecoder,
                             IncrementalEncoder as UTF8IncrementalEncoder)
import re
import codecs

NAME = 'utf-8-variants'
CESU8_RE = re.compile(b'\xed[\xa0-\xaf][\x80-\xbf]\xed[\xb0-\xbf][\x80-\xbf]')


# TODO: document and write tests
class IncrementalDecoder(UTF8IncrementalDecoder):
    def _buffer_decode(self, input, errors, final):
        decoded_segments = []
        position = 0
        while True:
            decoded, consumed = self._buffer_decode_step(
                input[position:],
                errors,
                final
            )
            if consumed == 0:
                break
            decoded_segments.append(decoded)
            position += consumed

        if final:
            assert position == len(input)
        return ''.join(decoded_segments), position

    def _buffer_decode_step(self, input, errors, final):
        sup = UTF8IncrementalDecoder._buffer_decode
        cutoff1 = input.find(b'\xed')
        cutoff2 = input.find(b'\xc0')
        if cutoff1 != -1 and cutoff2 != -1:
            cutoff = min(cutoff1, cutoff2)
        elif cutoff1 != -1:
            cutoff = cutoff1
        elif cutoff2 != -1:
            cutoff = cutoff2
        else:
            # The UTF-8 decoder can handle it from here.
            return sup(input, errors, final)

        if input.startswith(b'\xc0'):
            return self._buffer_decode_null(sup, input, errors, final)
        elif input.startswith(b'\xed'):
            return self._buffer_decode_surrogates(sup, input, errors, final)
        else:
            # at this point, we know cutoff > 0
            return sup(input[:cutoff], errors, False)

    @staticmethod
    def _buffer_decode_null(sup, input, errors, final):
        nextchar = input[1:2]
        if nextchar == b'':
            if final:
                return sup(input, errors, True)
            else:
                return '', 0
        elif nextchar == b'\x80':
            return '\u0000', 2
        else:
            return sup(b'\xc0', errors, True)

    @staticmethod
    def _buffer_decode_surrogates(sup, input, errors, final):
        """
        When we have improperly encoded surrogates, we can still see the
        bits that they were meant to represent.
        
        The surrogates were meant to encode a 20-bit number, to which we
        add 0x10000 to get a codepoint. That 20-bit number now appears in
        this form:
        
          11101101 1010abcd 10efghij 11101101 1011klmn 10opqrst
        
        The CESU8_RE above matches byte sequences of this form. Then we need
        to extract the bits and assemble a codepoint number from them.
        """
        if len(input) < 6:
            if final:
                return sup(input, errors, True)
            else:
                return '', 0
        else:
            if CESU8_RE.match(input):
                bytenums = bytes_to_ints(input[:6])
                codepoint = (
                    ((bytenums[1] & 0x0f) << 16) +
                    ((bytenums[2] & 0x3f) << 10) +
                    ((bytenums[4] & 0x0f) << 6) +
                    (bytenums[5] & 0x3f) +
                    0x10000
                )
                return unichr(codepoint), 6
            else:
                return sup(input[:3], errors, False)


# The encoder is identical to UTF8.
IncrementalEncoder = UTF8IncrementalEncoder


# Everything below here is basically boilerplate.
def encode(input, errors='strict'):
    return IncrementalEncoder(errors).encode(input, final=True), len(input)


def decode(input, errors='strict'):
    return IncrementalDecoder(errors).decode(input, final=True), len(input)


class StreamWriter(codecs.StreamWriter):
    encode = encode


class StreamReader(codecs.StreamReader):
    decode = decode


CODEC_INFO = codecs.CodecInfo(
    name=NAME,
    encode=encode,
    decode=decode,
    incrementalencoder=IncrementalEncoder,
    incrementaldecoder=IncrementalDecoder,
    streamreader=StreamReader,
    streamwriter=StreamWriter,
)
