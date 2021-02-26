# -*- coding: utf-8 -*-
from unittest import TestCase
from nlplib.facade import NlplibFacade
from nlplib.references import Reference
from nlplib import sentlevel_process


class ExtRefTest(TestCase):
    '''Tests for the External References extraction'''

    def test_simple_url(self):
        link = 'www.lawyermarketing.com//Acceptable-Use-Policy.shtml'
        facade = NlplibFacade(
            'Some url to test %s. Should be easy...' % link
        )
        self.assertIn(Reference(link, Reference.TYPE_URL, 17, 0), facade.external_references)

    def test_simple_email(self):
        email = 'google@gmail.com'
        facade = NlplibFacade(
            'Some email to test %s. Should be easy...' % email
        )
        self.assertIn(Reference(email, Reference.TYPE_EMAIL, 19, 0), facade.external_references)

    def test_unicode(self):
        email = 'google@gmail.com'
        text = u'Some “Master Agreement” email to "test" %s. Should be easy...' % email

        analysis, _ = sentlevel_process(text=text)
        self.assertIn({'reftype': 'Email', 'length': 16, 'form': u'google@gmail.com', 'offset': 40, 'sent_idx': 0},
                      analysis['sentences'][0]['external_refs'])

    def test_not_urls(self):
        facade = NlplibFacade(
            '''
            http https://  www. .com
            http:/no-tld
            ?daaa=aa
            should not be caught as refs
            '''
        )
        self.assertTrue(facade.external_references == [])

    def test_not_emails(self):
        facade = NlplibFacade(
            '''
            @ana  a @ gg .com ana@gmail.
            ?da@aa=a.a
            should not be caught as @refs@.com
            '''
        )
        self.assertTrue(facade.external_references == [])

    def test_standards(self):
        standard = 'Digital Millennium Copyright Act'
        facade = NlplibFacade(
            'Some standard to test %s. Should be easy...' % standard
        )
        self.assertIn(Reference(standard, Reference.TYPE_STANDARD, 22, 0), facade.external_references)
        self.assertEqual(facade.external_references[0].pos_start, 22)

    def test_local_offset(self):
        """
        Tests that the offset is correctly computed relative to the beginning of
        the sentence where the reference was found
        """
        link = 'www.lawyermarketing.com//Acceptable-Use-Policy.shtml'
        text = 'Should be easy. Some url to test %s. Should be easy...' % link

        analysis, _ = sentlevel_process(text=text)
        self.assertIn({'reftype': 'URL', 'length': 52, 'form': link, 'offset': 17, 'sent_idx': 1},
                      analysis['sentences'][1]['external_refs'])

    def test_offset_from_sentences(self):
        from nlplib.utils import split_sentences
        from core.models import multispaces_re

        link = 'www.vidyard.com'
        plaintext = (
u'''These Terms of Service (as defined below) are legally binding and govern all Your (as defined below) use of all Services (as defined below) offered by Buildscale Inc., operating as Vidyard, (“Buildscale”, “Our”, “Us” or “We”).

PLEASE READ THESE TERMS OF SERVICE CAREFULLY. THESE TERMS OF SERVICE SETS FORTH THE LEGALLY BINDING TERMS AND CONDITIONS FOR YOUR USE OF THE VIDYARD SERVICES AND INCLUDES GRANTS OF RIGHTS TO US AND LIMITATIONS ON OUR LIABILITY. YOU SHOULD PRINT A COPY OF THESE TERMS OR SAVE THEM ON YOUR DEVICE IN THE EVENT THAT YOU NEED TO REFER TO THEM IN THE FUTURE.
1. INTRODUCTION

1.1 Scope. The services offered by Buildscale include (collectively, “Services”): (i) those offered on any Vidyard-branded URL, including  www.vidyard.com (the “Website”);(ii) Vidyard (as defined below); (iii) the Player; (iv) Buildscale or Vidyard developer services; (v) Buildscale or Vidyard apps; (vi) technical support; (vii) Professional Services; and (vi) any other features, content, or applications offered or operated from time to time by Buildscale in connection with Buildscale’s business, including when Vidyard is accessed via the internet, mobile device, television or other device. These Terms of Service constitutes legally binding terms and applies to such use of the Services regardless of the type of device used to access them ("Device") unless such services post a different terms of use or end user license agreement, in which case that agreement ("Other Terms") shall instead govern. By accessing and/or using any of the Services, You agree to be bound by these Terms of Service (or if applicable, the Other Terms), whether You are a "Visitor" (which means that You simply browse the Services, including, without limitation, through a mobile or other wireless Device, or otherwise use the Services and/or access and view Content (as defined below) without being registered) or You are a "Customer" (which means that You have registered with Buildscale). The term "User" refers to a Visitor or a Customer. You are authorized to use the Services (regardless of whether Your access or use is intended) only if You agree to abide by all applicable laws, rules and regulations ("Applicable Law") and the terms of these Terms of Service. In addition, in consideration for becoming a Customer and/or making use of the Services, You must indicate Your acceptance of these Terms of Service during the registration process. Thereafter, You may create Your Account (as defined below), and its associated profile(s) in accordance with the terms herein.
'''
        )
        sentences = split_sentences(plaintext)
        sentences = [multispaces_re.sub(' ', s) for s in sentences]

        analysis, _ = sentlevel_process(sentences=sentences)
        self.assertIn({'reftype': 'URL', 'length': len(link), 'form': link, 'offset': 127, 'sent_idx': 6},
                      analysis['sentences'][6]['external_refs'])

    def test_offset_0(self):
        """
        Tests that the offset is correctly computed relative to the beginning of
        the sentence when the reference is the first word
        """
        link = 'www.lawyermarketing.com//Acceptable-Use-Policy.shtml'
        text = '%s is the link. Should be easy...' % link

        analysis, _ = sentlevel_process(text=text)
        self.assertIn({'reftype': 'URL', 'length': 52, 'form': link, 'offset': 0, 'sent_idx': 0},
                      analysis['sentences'][0]['external_refs'])

    def test_long_sent(self):
        link = 'http://www.youtube.com/t/terms'
        text = (
            u'(b) You represent and warrant that: (i) You own Your Content or '
            u'otherwise have the right to grant the licenses set forth in '
            u'Section 6.2(a), (ii) the uploading of Your Content on, through, '
            u'or in connection with the Services does not and will not violate '
            u'the privacy rights, personal, publicity rights, copyrights, '
            u'contract rights or any other rights of any Person; (iii) no fees '
            u'or payments of any kind shall be due by Buildscale to any '
            u'organization for the distribution of Your Content as contemplated '
            u'by these Terms of Service and You agree to pay for all royalties, '
            u'fees, and any other monies owing to any Person by reason of the '
            u'use of any Your Content; and (iv) if applicable, Your Content may '
            u'be uploaded and made publicly available on YouTube or similar '
            u'services, and that Your Content otherwise complies with YouTube’s '
            u'terms of service in effect from time to time, the current version '
            u'of which may be located at http://www.youtube.com/t/terms or the '
            u'terms of service of such other similar services to which Your '
            u'Content has been uploaded and made publicly available.'
        )

        analysis, _ = sentlevel_process(text=text)
        self.assertIn({'reftype': 'URL', 'length': 30, 'form': link, 'offset': 919, 'sent_idx': 0},
                      analysis['sentences'][0]['external_refs'])
