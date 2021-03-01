from unittest import skipIf
from django.conf import settings
from django.contrib.auth.models import User
from core.models import CollaborationInvite, Document
from dogbone.testing.base import BeagleLiveServerTestCase


class AccountPageLiveServerTestCase(BeagleLiveServerTestCase):
    @skipIf(getattr(settings, 'SKIP_SELENIUM_TESTS', False), "Skipping Selenium tests")
    def test_document_list_in_account_page(self):
        self.make_paid(self.user)
        document = Document.objects.create(original_name='Original.txt', title='Original.txt', owner=self.user, pending=False)

        self.live_login(self.DUMMY_EMAIL, self.DUMMY_PASSWORD)

        # Check that after login we arrive on the account page
        self.assertEqual(self.selenium.current_url, self.live_reverse('upload_file'))

        # Navigate to account page
        self.selenium.get(self.live_reverse('account'))

        self.wait_for_css('.project-title')

        # Check that we find our document in the list
        document_url_elem = self.selenium.find_element_by_xpath("//a[contains(.,'Original.txt')]")
        document_url_href = self.live_reverse('report', kwargs={'uuid': document.uuid})

        # Check that the link is the URL we expect for the document
        self.assertEqual(document_url_elem.get_attribute('href'), document_url_href)

        # Go to the report page
        document_url_elem.click()

        # Check we arrived at the correct URL
        self.assertEqual(self.selenium.current_url, document_url_href + '#/')

    @skipIf(getattr(settings, 'SKIP_SELENIUM_TESTS', False), "Skipping Selenium tests")
    def test_multiple_document_list_in_account_page(self):
        self.make_paid(self.user)

        # Create some documents
        self.create_analysed_document('doc1.txt', ['s1', 's2'], self.user)
        self.create_analysed_document('doc2.txt', ['s1', 's2'], self.user)
        self.create_analysed_document('doc3.txt', ['s1', 's2'], self.user)
        self.create_analysed_document('doc4.txt', ['s1', 's2'], self.user)

        self.live_login(self.DUMMY_EMAIL, self.DUMMY_PASSWORD)

        # Navigate to account page
        self.selenium.get(self.live_reverse('account'))

        # Get all the `.project-title` elements
        self.wait_for_css('.project-title')
        projects = self.selenium.find_elements_by_css_selector('.project-title')

        # Get the actual text
        project_titles = set([p.text for p in projects])

        # Compare to what is expected
        self.assertEqual(project_titles, set(['doc1.txt', 'doc2.txt', 'doc3.txt', 'doc4.txt']))

    @skipIf(getattr(settings, 'SKIP_SELENIUM_TESTS', False), "Skipping Selenium tests")
    def test_invited_to_document_in_account_page(self):
        self.make_paid(self.user)

        other_user = User.objects.create(email='other@email.com',
                                         username='the_other',
                                         password='p@$$')
        self.make_paid(other_user)

        document = self.create_analysed_document('the_doc.txt', ['s1', 's2'], other_user)

        CollaborationInvite.objects.create(inviter=other_user,
                                           invitee=self.user,
                                           document=document)

        self.live_login(self.DUMMY_EMAIL, self.DUMMY_PASSWORD)

        # Navigate to account page
        self.selenium.get(self.live_reverse('account'))

        self.wait_for_css('.project-title')
        invited_section = self.selenium.find_elements_by_css_selector('.projects-section.invited')[0]
        invited_to_projects = invited_section.find_elements_by_css_selector('.project-title')

        # Check that the title is there
        self.assertEqual(invited_to_projects[0].text, 'the_doc.txt')

        project_url = invited_to_projects[0].find_elements_by_css_selector('a')[0]

        project_url_href = project_url.get_attribute('href')

        # Check that the url is there
        self.assertEqual(project_url_href, self.live_reverse('report', kwargs={'uuid': document.uuid}))

        project_url.click()

        # Check we arrived at the correct URL
        self.assertEqual(self.selenium.current_url, project_url_href + '#/')
