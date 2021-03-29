if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from nltk import RegexpParser
from nlplib.utils import preprocess_text, sents2wordtag


grammar = '''
ABSOLUTE_RESPONSIBILITY:
    {<Agency__.*> <(Agrees|AGREES|agrees)__.*> <(Not|NOT|not)__.*> <(To|TO|to)__.*> <(Terminate|TERMINATE|terminate)__.*> <.*>* <(Unless|UNLESS|unless)__.*>}
'''


parser = RegexpParser(grammar)
parsed_sents = []

sentences = [
    u'Document to the contrary, the Agency agrees not to terminate the Letter of Credit unless (i) such termination is made in accordance with the terms of this Agreement, the Fee Agreement and the other Related Documents, (ii) the Agency provides fifteen (15) days prior written notice to the Bank in connection with any termination of the Letter of Credit and (iii) the Agency pays to the Bank, in connection with any termination of the Letter of Credit pursuant to the terms hereof, all fees, expenses and other Obligations payable hereunder or under the Fee Agreement, including, without limitation, all principal and accrued interest owing on any Bank Bonds and the payment of any fee associated therewith.'
]
sentences = list(map(preprocess_text, sentences))
wordtagged = sents2wordtag(sentences)

sentstyle = lambda x: ' '.join(list(map(lambda y: y[1].replace('__', '/'), x)))
for wt_sent in wordtagged:
    parsed_sents.append(parser.parse(wt_sent))

    # print sentstyle(parsed_sents[-1])
    print(parsed_sents[-1])
