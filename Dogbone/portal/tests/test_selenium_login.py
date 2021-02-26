from unittest import skipIf
from django.conf import settings
from dogbone.testing.base import BeagleLiveServerTestCase


class LoginLiveServerTestCase(BeagleLiveServerTestCase):
    @skipIf(getattr(settings, 'SKIP_SELENIUM_TESTS', False), "Skipping Selenium tests")
    def test_correct_login_credentials(self):
        self.selenium.get(self.live_reverse('login'))

        email_field = self.selenium.find_element_by_id("id_email")
        email_field.send_keys(self.DUMMY_EMAIL)

        password_field = self.selenium.find_element_by_id("id_password")
        password_field.send_keys(self.DUMMY_PASSWORD)

        submit_button = self.selenium.find_element_by_id("submit-button")
        submit_button.click()

        self.assertEqual(self.selenium.current_url, self.live_reverse('account'))

    @skipIf(getattr(settings, 'SKIP_SELENIUM_TESTS', False), "Skipping Selenium tests")
    def test_wrong_login_credentials(self):
        self.selenium.get(self.live_reverse('login'))

        email_field = self.selenium.find_element_by_id("id_email")
        email_field.send_keys(self.DUMMY_EMAIL)

        password_field = self.selenium.find_element_by_id("id_password")
        password_field.send_keys('how cute ... BUT IT\'S WRONG!!!')

        submit_button = self.selenium.find_element_by_id("submit-button")
        submit_button.click()

        self.assertEqual(self.selenium.current_url, self.live_reverse('login'))

        # This throws a NoSuchElementException if no element containing the text "Invalid email or password" was found
        self.selenium.find_element_by_xpath("//div[contains(.,'Invalid email or password')]")

    @skipIf(getattr(settings, 'SKIP_SELENIUM_TESTS', False), "Skipping Selenium tests")
    def test_already_logged_in(self):
        self.live_login(self.DUMMY_EMAIL, self.DUMMY_PASSWORD)
        self.selenium.get(self.live_reverse('login'))
        self.assertEqual(self.selenium.current_url, self.live_reverse('account'))
