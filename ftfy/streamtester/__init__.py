"""
This file defines a general method for evaluating ftfy using data that arrives
in a stream. A concrete implementation of it is found in `twitter_tester.py`.
"""
from __future__ import print_function, unicode_literals
from ftfy.fixes import fix_encoding
from ftfy.chardata import possible_encoding


class StreamTester:
    """
    Take in a sequence of texts, and show the ones that will be changed by
    ftfy. This will also periodically show updates, such as the proportion of
    texts that changed.
    """
    def __init__(self):
        self.num_fixed = 0
        self.count = 0

    def check_ftfy(self, text):
        """
        Given a single text input, check whether `ftfy.fix_text_encoding`
        would change it. If so, display the change.
        """
        self.count += 1
        if not possible_encoding(text, 'ascii'):
            fixed = fix_encoding(text)
            if text != fixed:
                # possibly filter common bots before printing
                print(u'\nText:\t{text}\nFixed:\t{fixed}\n'.format(
                    text=text, fixed=fixed
                ))
                self.num_fixed += 1

        # Print status updates once in a while
        if self.count % 100 == 0:
            print('.', end='', flush=True)
        if self.count % 10000 == 0:
            print('\n%d/%d fixed' % (self.num_fixed, self.count))
