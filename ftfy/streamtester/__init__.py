from __future__ import print_function, unicode_literals
from ftfy.fixes import fix_text_encoding
from ftfy.chardata import possible_encoding


class StreamTester:
    """
    Take in a sequence of texts, and show the ones that will be changed by ftfy.
    This will also periodically show updates, such as the proportion of texts that
    changed.
    """
    def __init__(self):
        self.num_fixed = 0
        self.count = 0

    def check_ftfy(self, text):
        self.count += 1
        if not possible_encoding(text, 'ascii'):
            fixed = fix_text_encoding(text)
            if text != fixed:
                # possibly filter common bots before printing
                print(u'\nText:\t{text}\nFixed:\t{fixed}\n'.format(text=text, fixed=fixed))
                self.num_fixed += 1
        if self.count % 100 == 0:
            print('.', end='')
        if self.count % 10000 == 0:
            print('\n%d/%d fixed' % (self.num_fixed, self.count))
