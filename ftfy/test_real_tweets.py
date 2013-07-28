# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy.fixes import fix_text_encoding
from nose.tools import eq_

TEST_CASES = [
    ("He's Justinâ¤", "He's Justin❤"),
    ("Le Schtroumpf Docteur conseille g√¢teaux et baies schtroumpfantes pour un r√©gime √©quilibr√©.",
     "Le Schtroumpf Docteur conseille gâteaux et baies schtroumpfantes pour un régime équilibré."),
    #("Deja dos heridos hundimiento de barco tur\x92stico en Acapulco.",
    # "Deja dos heridos hundimiento de barco turístico en Acapulco."),
    ("âœ” No problems", "✔ No problems"),
    ('4288×…', '4288×…'),
    ("РґРѕСЂРѕРіРµ РР·-РїРѕРґ http://t.co/A0eJAMTuJ1 #С„СѓС‚Р±РѕР»",
     "дороге Из-под http://t.co/A0eJAMTuJ1 #футбол"),
    ("Hi guys í ½í¸", "Hi guys 😍"),
    ("\x84Handwerk bringt dich \xfcberall hin\x93: Von der YOU bis nach Monaco",
     '„Handwerk bringt dich überall hin“: Von der YOU bis nach Monaco')
]

def test_real_tweets():
    for orig, target in TEST_CASES:
        eq_(fix_text_encoding(orig), target)