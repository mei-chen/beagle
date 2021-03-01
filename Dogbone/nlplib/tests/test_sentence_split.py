# -*- coding: utf-8 -*-

from unittest import TestCase
from nlplib.utils import is_title, split_sentences


class SentSplitTest(TestCase):
    def test_split(self):
        txt = u'''
This Agreement covers the provisions of broadband access, Internet, voice, data, Managed Broadband Services, Hosting Services, Applications and Voice-Over-IP and all others services ("Services") from Blackfoot pursuant to orderslaced by Customer and accepted by Blackfoot, as defined below and described in one or more Service Order Forms executed by Customer and Blackfoot (“Service Orders”). This Agreement includes each such Service Order, including any attachments or exhibits thereto, and all of the attachments to this Agreement. Please note that underlined terms in this Agreement are links to pages and websites where such attachments, each of which is incorporated herein by reference, may be reviewed by Customer.

CUSTOMER MUST READ, AGREE WITH AND ACCEPT ALL OF THE TERMS AND CONDITIONS OF THIS AGREEMENT, INCLUDING THE SERVICE ORDERS AND ATTACHMENTS INCORPORATED HEREIN BY REFERENCE, BEFORE USING OR ACCEPTING ANY BLACKFOOT SERVICES. IF CUSTOMER DOES NOT AGREE TO BE BOUND BY THE TERMS AND CONDITIONS OF THIS AGREEMENT, CUSTOMER MAY NOT, AND SHALL HAVE NO RIGHT TO, USE ANY BLACKFOOT SERVICES.



By accepting this Agreement, Customer agrees that its use of our Services will be governed by, and in accordance with, the terms and conditions hereof. Blackfoot may amend this Agreement at any time by posting the amended terms on its web site. All amended terms shall become effective upon Blackfoot posting such amended Agreement on its web site.
'''
        sentences = split_sentences(txt)
        self.assertEqual(len(sentences), 8)
        self.assertEqual(''.join(sentences), txt)

    def test_split_quote(self):
        txt = u'It\'s "confidential." More text.'
        sentences = split_sentences(txt)
        self.assertEqual(len([s for s in sentences if s]), 2)

    def test_split_unicode(self):
        """ Check that it doesn't blow up when fed unicode """
        split_sentences(u'All information regarding either Party’s business which has been marked or is otherwise communicated as being “proprietary” or “confidential.”')

    # --- Specific test cases ---

    def test_not_splitting_on_inc(self):
        texts = [
            'Beagle Inc. will do that.',
            'Blackfoot Communications, Inc.("Blackfoot"), provides services to its customers ("Customer").'
        ]

        for txt in texts:
            sentences = split_sentences(txt)
            self.assertEqual(len([s for s in sentences if s]), 1)

    def test_not_splitting_on_bullets(self):
        """ Some '. 's should not be sentence splitters """
        texts = [
            '- Beagle will do that.',
            '10. Beagle will do that.',
            'i. Blackleg Communications provides services to its customers ("Customer").',
            'iii. Communications provides services',
            'a. Communications provides services',
            'D. Communications provides services.',
            'et. al. etc. these are valid',
        ]

        for txt in texts:
            sentences = split_sentences(txt)
            self.assertEqual(len([s for s in sentences if s]), 1)

    def test_not_splitting_on_acronyms(self):
        """ Some '. 's should not be sentence splitters """
        texts = [
            'Inc. brand.',
            'Beagle Inc. will do that.',
            'BEAGLE INC. DOES EVERYTHING.',
            'Beagle Inc. COMMUNICATIONS PROVIDES SERVICES',
            u'This Master Subscription Agreement (the "Agreement") is entered into as of ____________, 2015 (“Effective Date”) by and between Axonify Inc., a Canadian Corporation having its registered office at 460 Phillip St. Suite 300, Waterloo, ON N2L 5J2 ("Axonify Inc.") and Shinydocs Corporation having its principal place of business at 108 Ahrens St W #8b, Kitchener, ON N2H 4C3 ("Customer").',
            u'This Master Services Agreement (the “Agreement” or "MSA") describes the terms on which Blackfoot Communications, Inc. (“Blackfoot”), provides services to its customers ("Customer").',
            u'The Subscriber acknowledges that the Securities have not been and will not be registered under the United States Securities Act of 1933, as amended, (the “U.S. Securities Act”) or the securities laws of any state and that these securities may not be offered or sold in the United States without registration under the U.S. Securities Act or compliance with requirements of an exemption from registration, and the applicable laws of all applicable states or an exemption from such registration requirements is available.',
            u'The Subscriber acknowledges that the Corporation has no present intention of filing a registration statement under the U.S. Securities Act in respect of the Securities.',
        ]

        for txt in texts:
            sentences = split_sentences(txt)
            self.assertEqual(len([s for s in sentences if s]), 1)

    def test_not_splitting_on_name_abbreviations(self):
        text = u'Roy T. Englert, Jr., argued the cause for petitioner. With him on the briefs was Melissa B. Rogers. Pamela Y. Price argued the cause for respondent. With her on the brief were Howard J. Moore, Jr., and William McNeill III. Austin C. Schlick argued the cause for the United States as amicus curiae urging reversal. With him on the brief were Solicitor General Olson, Acting Assistant Attorney General Schiffer, Deputy Solicitor General Clement, Marleigh D. Dover, and John C. Hoyle...'
        expected_sentences = [
            u'Roy T. Englert, Jr., argued the cause for petitioner. ',
            u'With him on the briefs was Melissa B. Rogers. ',
            u'Pamela Y. Price argued the cause for respondent. ',
            u'With her on the brief were Howard J. Moore, Jr., and William McNeill III. ',
            u'Austin C. Schlick argued the cause for the United States as amicus curiae urging reversal. ',
            u'With him on the brief were Solicitor General Olson, Acting Assistant Attorney General Schiffer, Deputy Solicitor General Clement, Marleigh D. Dover, and John C. Hoyle...',
        ]
        actual_sentences = split_sentences(text)
        self.assertEqual(expected_sentences, actual_sentences)

    def test_not_splitting_on_particular_abbreviations(self):
        text = u'The Court\'s holding does not leave employers defenseless when a plaintiff unreasonably delays filing a charge. The filing period is subject to waiver, estoppel, and equitable tolling when equity so requires, Zipes, supra, at 398, and an employer may raise a laches defense if the plaintiff unreasonably delays in filing and as a result harms the defendant, see, e. g., Albemarle Paper Co. v. Moody, 422 U. S. 405, 424-425. Pp. 121-122.'
        expected_sentences = [
            u'The Court\'s holding does not leave employers defenseless when a plaintiff unreasonably delays filing a charge. ',
            u'The filing period is subject to waiver, estoppel, and equitable tolling when equity so requires, Zipes, supra, at 398, and an employer may raise a laches defense if the plaintiff unreasonably delays in filing and as a result harms the defendant, see, e. g., Albemarle Paper Co. v. Moody, 422 U. S. 405, 424-425. ',
            u'Pp. 121-122.',
        ]
        actual_sentences = split_sentences(text)
        self.assertEqual(expected_sentences, actual_sentences)

    def test_not_merging_wanted_splits(self):
        """ Assert the merger is not too permisive """
        texts = [
            'Ahoy. Howdy?',
            '$60. Damn bike rental!',
            'mahjong. Communications provides services',
        ]

        for txt in texts:
            sentences = split_sentences(txt)
            self.assertEqual(len([s for s in sentences if s]), 2)

    def test_bullets_merge(self):
        txt = u'''Non-Solicitation. 
20. Any attempt.'''
        sentences = split_sentences(txt)
        self.assertEqual(sentences, [u'Non-Solicitation. \n', u'20. Any attempt.'])

    def test_bslashr(self):
        txt = u'''Non-Solicitation.\r20. Any attempt.'''
        sentences = split_sentences(txt)
        self.assertEqual(sentences, [u'Non-Solicitation.\r', u'20. Any attempt.'])

    def test_split_title(self):
        txt = u'''
            Terms of Agreement
            This Terms of Agreement, including its Addenda and Schedules governs terms and conditions between X, Y and Z.
            1. Definitions
            1.1. Acceptable Use Policy means the applicable terms and conditions governing the use by End Users of a specific Product, Service or Application, as may be identified on the Fees and Rates Schedule.
            1.2. Active User means a License Model that accounts for any person who registers for or is enrolled in one or more courses in each consecutive 12-month period following the Effective Date.
            This sentence was intentionally split into two lines,
            and it doesn't contain any title.
        '''
        sentences = split_sentences(txt)
        self.assertEqual(len(sentences), 6)
        self.assertEqual(''.join(sentences), txt)

    def check_is_title(self, clause, expected):
        actual = is_title(clause)
        self.assertEqual(expected, actual)

    def test_is_title(self):
        self.check_is_title(' \t \n \t ', False)
        self.check_is_title('', False)

        self.check_is_title('London is the capital of Great Britain', False)

        self.check_is_title('Python for Biologists', True)
        self.check_is_title('Learn Python the Hard Way', True)
        self.check_is_title('Hacking Secret Ciphers with Python', True)
        self.check_is_title('Automate the Boring Stuff with Python', True)

        for clause in ['Definitions',
                       'Billing and Payment Terms',
                       'Description of Services, Rates and Charges',
                       'Use of the Service Offerings',
                       'Security and Data Privacy',
                       'Owner\'s Representative; Inspection of Work',
                       'Dispute Resolution and Governing Law',
                       'Disclaimers and Limitations of Liability',
                       'Compliance with Applicable Laws',
                       'Ownership and Intellectual Property Rights',
                       'Account Termination Policy',
                       'Copyright Notice']:

            for bullet in ['1', 'iv', 'G', 'c', '7', 'XI', 'v', '9', 'N']:
                self.check_is_title('\t%s. %s\n' % (bullet, clause), True)
                self.check_is_title('\t%s. %s:\n' % (bullet, clause), False)
                self.check_is_title('\t%s. \n' % bullet, False)

            self.check_is_title(clause, True)
            self.check_is_title(clause.lower(), False)
            self.check_is_title(clause.upper(), len(clause.split()) <= 4)
