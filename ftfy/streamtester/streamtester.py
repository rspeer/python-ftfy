from twitter import TwitterStream, OAuth
import json
import time
import unicodedata
import os
from ftfy.fixes import fix_text_encoding, remove_unsafe_private_use
from ftfy.badness import sequence_weirdness
from ftfy.chardata import possible_encoding
from ftfy.streamtester.oauth import get_auth
from collections import defaultdict

OUTPUT_DIR = './twitterlogs'
class TwitterTester:
    def __init__(self):
        self.lines_by_lang = defaultdict(list)
        self.num_fixed = 0

    def save_files(self):
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        for lang, lines in self.lines_by_lang.items():
            filename = 'tweets.{}.txt'.format(lang)
            fullname = os.path.join(OUTPUT_DIR, filename)
            langfile = open(fullname, 'a')
            for line in lines:
                print(line.replace('\n', ' '), file=langfile)
            langfile.close()
        self.lines_by_lang = defaultdict(list)

    def run_sample(self):
        twitter_stream = TwitterStream(auth=get_auth())
        iterator = twitter_stream.statuses.sample()
        count = 0
        for tweet in iterator:
            if 'text' in tweet:
                self.handle_tweet(tweet)
            if count % 10000 == 0:
                print('%d/%d fixed' % (self.num_fixed, count))
            count += 1
            if count % 10000 == 100:
                self.save_files()

    def check_ftfy(self, text):
        if not possible_encoding(text, 'ascii'):
            fixed = fix_text_encoding(text)
            if text != fixed:
                # possibly filter common bots before printing
                print(u'Text:\t{text}\nFixed:\t{fixed}\n'.format(text=text, fixed=fixed))
                self.num_fixed += 1

    def handle_tweet(self, tweet):
        text = tweet['text']
        self.check_ftfy(text)
        if 'user' in tweet:
            lang = tweet['user'].get('lang', 'NONE')
            self.lines_by_lang[lang].append(tweet['text'])


def main():
    tester = TwitterTester()
    tester.run_sample()


if __name__ == '__main__':
    main()

