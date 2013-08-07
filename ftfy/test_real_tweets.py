# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ftfy import fix_text
from nose.tools import eq_

TEST_CASES = [
    ("He's Justinâ¤", "He's Justin❤"),
    ("Le Schtroumpf Docteur conseille g√¢teaux et baies schtroumpfantes pour un r√©gime √©quilibr√©.",
     "Le Schtroumpf Docteur conseille gâteaux et baies schtroumpfantes pour un régime équilibré."),
    #("Deja dos heridos hundimiento de barco tur\x92stico en Acapulco.",
    # "Deja dos heridos hundimiento de barco turístico en Acapulco."),
    ("âœ” No problems", "✔ No problems"),
    ('4288×…', '4288×...'),
    ('RETWEET SE VOCÊ…', 'RETWEET SE VOCÊ...'),
    ('PARCE QUE SUR LEURS PLAQUES IL Y MARQUÉ…', 'PARCE QUE SUR LEURS PLAQUES IL Y MARQUÉ...'),
    ('Join ZZAJÉ’s Official Fan List and receive news, events, and more!', "Join ZZAJÉ's Official Fan List and receive news, events, and more!"),
    ('L’épisode 8 est trop fou ouahh', "L'épisode 8 est trop fou ouahh"),
    ("РґРѕСЂРѕРіРµ РР·-РїРѕРґ http://t.co/A0eJAMTuJ1 #С„СѓС‚Р±РѕР»",
     "дороге Из-под http://t.co/A0eJAMTuJ1 #футбол"),
    ("\x84Handwerk bringt dich \xfcberall hin\x93: Von der YOU bis nach Monaco",
     '"Handwerk bringt dich überall hin": Von der YOU bis nach Monaco'),
    ("Hi guys í ½í¸", "Hi guys 😍"),
    ("@rakryanM hihi RT damnitstrue: âºí ½í¸ http://t.co/DqSCy26POe",
     "@rakryanM hihi RT damnitstrue: ☺😘 http://t.co/DqSCy26POe"),
    ("Beta Haber: HÄ±rsÄ±zÄ± BÃ¼yÃ¼ Korkuttu http://t.co/rMkt5yz7Si",
     "Beta Haber: Hırsızı Büyü Korkuttu http://t.co/rMkt5yz7Si"),
]

def test_real_tweets():
    """
    Test with text actually found on Twitter.

    I collected these test cases by listening to the Twitter streaming API for
    a million or so tweets, picking out examples with high weirdness according
    to ftfy version 2, and seeing what ftfy decoded them to. There are some
    impressive things that can happen to text, even in an ecosystem that is
    supposedly entirely UTF-8.

    The tweets that appear in TEST_CASES are the most interesting examples of
    these, with some trickiness of how to decode them into the actually intended
    text.
    """
    for orig, target in TEST_CASES:
        # make sure we can decode the text as intended
        eq_(fix_text(orig), target)

        # make sure we can decode as intended even with an extra layer of badness
        extra_bad = orig.encode('utf-8').decode('latin-1')
        eq_(fix_text(extra_bad), target)
