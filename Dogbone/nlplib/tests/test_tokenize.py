# -*- coding: utf-8 -*-

from unittest import TestCase

from nlplib.utils import preprocess_text, sents2wordtag


class TokenizeTokenizeTest(TestCase):

    def test_tokenize(self):
        txt = u'''
Blackfoot, as defined below and described in one or more Service Order Forms executed by Customer and Blackfoot (“Service Orders”).
'''
        expected_toks = ['Blackfoot', ',', 'as', 'defined', 'below', 'and', 'described', 'in', 'one', 'or', 'more', 'Service', 'Order', 'Forms', 'executed', 'by', 'Customer', 'and', 'Blackfoot', '_LPAR_', '"', 'Service', 'Orders', '"', '_RPAR_', '.']
        actual_toks = [tok for tok, tagged in sents2wordtag([preprocess_text(txt)])[0]]
        self.assertEqual(expected_toks, actual_toks)
