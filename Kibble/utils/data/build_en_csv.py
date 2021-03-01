import codecs
import re

non_alphanumeric_re = re.compile(r'\W', re.UNICODE)

def process(word):
    word = word.strip().split('/')[0]
    if not word:  # skip empty
        return ''
    if non_alphanumeric_re.match(word[0]):  # skip non-alphanumeric beginnings
        return ''
    if word[0].isdigit():  # skip numbers and numerals
        return ''
    if not word.islower():  # skip proper names, abbreviations, etc.
        return ''
    return word

words = set()

with codecs.open('en_GB.dic', mode='rb', encoding='cp1252') as en_gb:
    for word in en_gb:
        word = process(word)
        if word:
            words.add(word)

with codecs.open('en_US.dic', mode='rb', encoding='utf8') as en_us:
    for word in en_us:
        word = process(word)
        if word:
            words.add(word)

words = sorted(words)

with codecs.open('en.csv', mode='wb', encoding='utf8') as en:
    for word in words:
        en.write(word)
        en.write('\n')
