# -*- coding: utf-8 -*-
from __future__ import unicode_literals

TEST_CASES = [
    ("He's Justinâ¤", "He's Justin❤"),
    ("Le Schtroumpf Docteur conseille g√¢teaux et baies schtroumpfantes pour un r√©gime √©quilibr√©.",
     "Le Schtroumpf Docteur conseille gâteaux et baies schtroumpfantes pour un régime équilibré."),
    ("Deja dos heridos hundimiento de barco tur\x92stico en Acapulco.",
     "Deja dos heridos hundimiento de barco turístico en Acapulco."),
    ("âœ” No problems", "✔ No problems"),
    ('4288×…', '4288×…'),
    ("РґРѕСЂРѕРіРµ РР·-РїРѕРґ http://t.co/A0eJAMTuJ1 #С„СѓС‚Р±РѕР»",
     "дороге Из-под http://t.co/A0eJAMTuJ1 #футбол"),
    ("Hi guys í ½í¸", "Hi guys 😍"),
    ("\x84Handwerk bringt dich \xfcberall hin\x93: Von der YOU bis nach Monaco",
     '„Handwerk bringt dich überall hin“: Von der YOU bis nach Monaco')
]


# Possible cases:
# (1) Actual text is UTF-8. Decoded in 1-byte encoding.
#     - Use a heuristic to shrink the text size and decrease badness.
#     - It will work very consistently if it works.
# (2) Actual text is in a 1-byte encoding, but was decoded with a different one.
#     - Use a single-byte heuristic if it helps. Prefer to leave the text alone.
# (3) Text is in a mix of Windows-1252 and Latin-1.
#     - Replace control characters with Windows-1252 equivalents and proceed.
# (4) Text is in a mix of Windows-1251 and Latin-1.
#     - Oh wow. But, same deal.

# Strategy:
#   If maxchar < 128:
#     ASCII! \o/
#   If maxchar < 256:
#     Try Latin-1 => UTF-8.
#   If all chars in Latin-1 + Windows-1252:
#     Convert Latin-1 control characters to Windows-1252.
#     Try Windows-1252 => UTF-8.
#     Try other 1-byte encodings.
#   If all chars in another 1-byte encoding:
#     Try other 1-byte encodings.
#
# UTF-8 heuristic:
#   * How many positive examples?
#   * How many script clashes were introduced?
#   * No failures?
#   * Did it create modifiers out of nowhere?
