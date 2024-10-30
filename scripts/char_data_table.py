"""
Used to regenerate character tables in ftfy/chardata.py with explanatory comments.
"""

import unicodedata
from dataclasses import dataclass

from ftfy.chardata import UTF8_CLUES


@dataclass
class CharData:
    name: str
    codept: int
    encodings: list[tuple[str, int]]

    def sort_key(self) -> tuple[int, str, int]:
        if self.name.startswith("LATIN "):
            return (0, self.name, self.codept)
        return (1, "", self.codept)


SAFE_ENCODINGS = [
    "latin-1",
    "windows-1252",
    "windows-1251",
    "windows-1250",
    "windows-1253",
    "windows-1254",
    "windows-1257",
]


def show_char_table(chars: str, byte_min: int = 0, byte_max: int = 0xFF) -> None:
    char_data: list[CharData] = []
    for char in chars:
        name = unicodedata.name(char, "<unknown>")
        codept = ord(char)
        encodings: list[tuple[str, int]] = []
        for encoding in SAFE_ENCODINGS:
            try:
                encoded: bytes = char.encode(encoding)
                byte: int = encoded[0]
                encodings.append((encoding, byte))
            except UnicodeEncodeError:
                pass
        if encodings:
            char_data.append(CharData(name=name, codept=codept, encodings=encodings))
        else:
            print(f"No relevant encoding for {codept=}, {name=}")
    char_data.sort(key=CharData.sort_key)
    for cd in char_data:
        encoding_info: list[str] = []
        for encoding, byte in cd.encodings:
            if byte_min <= byte <= byte_max:
                info_str = f"{encoding}:{byte:X}"
                encoding_info.append(info_str)
        encoding_explanation = encoding_info[0] if encoding_info else "???"
        print(f'        "\\N{{{cd.name}}}"  # {encoding_explanation}')


def run() -> None:
    print("# utf8_first_of_2")
    show_char_table(UTF8_CLUES["utf8_first_of_2"], 0xC2, 0xDF)
    print("# utf8_first_of_3")
    show_char_table(UTF8_CLUES["utf8_first_of_3"], 0xE0, 0xEF)
    print("# utf8_first_of_4")
    show_char_table(UTF8_CLUES["utf8_first_of_4"], 0xF0, 0xF3)
    print("# utf8_continuation")
    print(r'        "\x80-\xbf"')
    show_char_table(UTF8_CLUES["utf8_continuation"][3:], 0x80, 0xBF)
    print("# utf8_continuation_strict")
    print(r'        "\x80-\xbf"')
    show_char_table(UTF8_CLUES["utf8_continuation_strict"][3:], 0x80, 0xBF)


if __name__ == "__main__":
    run()
