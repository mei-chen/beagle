import os
import email
from dogbone.testing.base import BeagleWebTest
from rufus.tools import get_body


class RufusTestCase(BeagleWebTest):
    def setUp(self):
        self.CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
        self.TEST_EMAIL_FOLDER = os.path.join(self.CURRENT_FOLDER, 'test_emails')
        self.COMPLICATED_FORMATTING = 'complicated_formatting.email'

        super(RufusTestCase, self).setUp()

    def test_get_body(self):
        raw_msg = open(os.path.join(self.TEST_EMAIL_FOLDER, self.COMPLICATED_FORMATTING), 'rb').read()
        msg = email.message_from_string(raw_msg)
        body = get_body(msg)

        for sentence in ["Privacy Policy",

                         "Your privacy is important to Apple. So we've developed a Privacy Policy that covers "
                         "how we collect, use, disclose, transfer, and store your information. Please take a moment "
                         "to familiarize yourself with our privacy practices and let us know if you have any questions.",

                         "Collection and Use of Personal Information",

                         "Personal information is data that can be used to identify or contact a single person."]:

            self.assertIn(sentence, body)