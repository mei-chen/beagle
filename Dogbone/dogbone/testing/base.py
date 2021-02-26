import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase, LiveServerTestCase
import mock
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

# App
from core.models import Document, Batch
from dogbone.app_settings.marketing_settings import (
    YearlyPaidSubscription, UnlimitedBrowserExtensionSubscription
)
from marketing.models import PurchasedSubscription
from user_sessions.utils.tests import Client as UserSessionClient


class BeagleWebTest(TestCase):
    NEED_DEFAULT_USER = True

    DUMMY_PASSWORD = 'dummyp@ss'
    DUMMY_USERNAME = 'dummy_user'
    DUMMY_EMAIL = 'dummy@email.com'

    DUMMY_TEXT_FILE = """
    This is a sample text file.
    There are 2 parties: PARTY1 and PARTY2
    """

    client_class = UserSessionClient

    DUMMY_TEXT_FILE_NAME = 'Sample_file.txt'

    @classmethod
    def setUpClass(cls):
        super(BeagleWebTest, cls).setUpClass()

        if cls.NEED_DEFAULT_USER:
            # Create a single test user for the whole test case (one per class).
            # Since the user is a singleton, it should be treated as immutable.
            # If you want your test user to get changed during testing, then you
            # may set NEED_DEFAULT_USER = False in a derived subclass and create
            # a test user inside the setUp method (one per method).
            cls.user = cls.create_user()
        else:
            cls.user = None

        # Mock and thus disable the cache
        cls.cache_get_patcher = mock.patch(
            'django.core.cache.cache.get',
            side_effect=lambda *args, **kwargs: None
        )
        cls.cache_set_patcher = mock.patch(
            'django.core.cache.cache.set',
            side_effect=lambda *args, **kwargs: None
        )
        cls.cache_delete_patcher = mock.patch(
            'django.core.cache.cache.delete',
            side_effect=lambda *args, **kwargs: None
        )

        cls.cache_get_patcher.start()
        cls.cache_set_patcher.start()
        cls.cache_delete_patcher.start()

        # Mock and thus disable some middleware classes
        cls.user_time_zone_middleware_patcher = mock.patch(
            'portal.middleware.UserTimezoneMiddleware.process_request',
            side_effect=lambda *args, **kwargs: None
        )
        cls.visitor_tracking_middleware_patcher = mock.patch(
            'tracking.middleware.VisitorTrackingMiddleware.process_request',
            side_effect=lambda *args, **kwargs: None
        )

        cls.user_time_zone_middleware_patcher.start()
        cls.visitor_tracking_middleware_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.visitor_tracking_middleware_patcher.stop()
        cls.user_time_zone_middleware_patcher.stop()

        cls.cache_delete_patcher.stop()
        cls.cache_set_patcher.stop()
        cls.cache_get_patcher.stop()

        if cls.user:
            cls.user.delete()

        super(BeagleWebTest, cls).tearDownClass()

    def login(self, username=DUMMY_USERNAME, password=DUMMY_PASSWORD):
        self.client.login(username=username, password=password)

    def logout(self):
        self.client.logout()

    @classmethod
    def get_temporary_text_file(cls, title=None, content=None):
        if title is None:
            title = cls.DUMMY_TEXT_FILE_NAME
        if content is None:
            content = cls.DUMMY_TEXT_FILE

        io = StringIO.StringIO()
        io.write(content)
        text_file = InMemoryUploadedFile(io, None, title, 'text/plain', io.len, None)
        text_file.seek(0)
        return text_file

    @staticmethod
    def create_batch(name, owner, pending=True):
        return Batch.objects.create(name=name, owner=owner, pending=pending)

    @staticmethod
    def create_document(title, owner, batch=None, pending=True):
        d = Document(original_name=title + '.pdf',
                     title=title,
                     agreement_type=Document.GENERIC,
                     owner=owner,
                     pending=pending,
                     batch=batch)
        d.init([title + ' ' + title], None, None)
        d.save()
        return d

    @staticmethod
    def create_analysed_document(original_filename, sentences, owner, batch=None):
        from core.tasks import process_document_task

        d = Document(owner=owner,
                     original_name=original_filename,
                     title=original_filename,
                     docx_s3=None,
                     pdf_s3=None,
                     pending=True,
                     batch=batch)
        d.init(sentences)
        d.save()

        process_document_task(d.pk, False, False, True)
        d = Document.objects.get(pk=d.pk)
        return d

    @staticmethod
    def create_user(email=DUMMY_EMAIL, username=DUMMY_USERNAME,
                    password=DUMMY_PASSWORD, **attrs):
        user = User(username=username, email=email)
        user.set_password(password)
        for attr_name, attr_value in attrs.items():
            setattr(user, attr_name, attr_value)
        user.save()
        return user

    @staticmethod
    def make_paid(user):
        PurchasedSubscription.purchase_subscription(user, YearlyPaidSubscription)

    @staticmethod
    def make_extension_user(user):
        PurchasedSubscription.purchase_subscription(user, UnlimitedBrowserExtensionSubscription)

    @staticmethod
    def add_to_group(user, group_name):
        g, _ = Group.objects.get_or_create(name=group_name)
        g.user_set.add(user)


class MultiUserBeagleWebTest(BeagleWebTest):
    USER2_EMAIL = 'ihaveadummy@email.com'
    USER2_USERNAME = 'iamadummy'
    USER2_PASSWORD = 'dummypassword'

    @classmethod
    def setUpClass(cls):
        super(MultiUserBeagleWebTest, cls).setUpClass()

        cls.make_paid(cls.user)

        cls.user2 = cls.create_user2()

        cls.make_paid(cls.user2)

        cls.client2 = cls.client_class()

    @classmethod
    def tearDownClass(cls):
        cls.user2.delete()

        super(MultiUserBeagleWebTest, cls).tearDownClass()

    @classmethod
    def create_user2(cls):
        return cls.create_user(cls.USER2_EMAIL, cls.USER2_USERNAME,
                               cls.USER2_PASSWORD)

    def login_user2(self):
        self.client2.login(username=self.USER2_USERNAME,
                           password=self.USER2_PASSWORD)

    def logout_user2(self):
        self.client2.logout()


class MockResponse:
    def __init__(self, content, status_code, headers={}):
        self.content = content
        self.status_code = status_code
        self.headers = headers


class BeagleLiveServerTestCase(LiveServerTestCase):
    DUMMY_PASSWORD = 'dummyp@ss'
    DUMMY_USERNAME = 'dummy_user'
    DUMMY_EMAIL = 'dummy@email.com'

    @classmethod
    def setUpClass(cls):
        super(BeagleLiveServerTestCase, cls).setUpClass()

        cls.user = User.objects.create_user(username=cls.DUMMY_USERNAME,
                                            email=cls.DUMMY_EMAIL,
                                            password=cls.DUMMY_PASSWORD)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

        super(BeagleLiveServerTestCase, cls).tearDownClass()

    def setUp(self):
        super(BeagleLiveServerTestCase, self).setUp()

        self.selenium = settings.SELENIUM_WEBDRIVER['webdriver_type'](
            executable_path=settings.SELENIUM_WEBDRIVER['webdriver_path']
        )

        self.selenium.maximize_window()

    def tearDown(self):
        self.selenium.quit()

        super(BeagleLiveServerTestCase, self).tearDown()

    def live_reverse(self, *args, **kwargs):
        return self.live_server_url + reverse(*args, **kwargs)

    def find_css(self, css_selector):
        """ Shortcut to find elements by CSS. Returns either a list or a singleton. """
        elems = self.selenium.find_elements_by_css_selector(css_selector)
        found = len(elems)
        if found == 1:
            return elems[0]
        elif not elems:
            raise NoSuchElementException(css_selector)
        return elems

    def wait_for_css(self, css_selector, timeout=7):
        """ Shortcut for WebDriverWait"""
        return WebDriverWait(self, timeout).until(lambda driver: driver.find_css(css_selector))

    def live_login(self, email, password):
        self.selenium.get(self.live_reverse('login'))

        email_field = self.selenium.find_element_by_id("id_email")
        email_field.send_keys(email)

        password_field = self.selenium.find_element_by_id("id_password")
        password_field.send_keys(password)

        submit_button = self.selenium.find_element_by_id("submit-button")
        submit_button.click()

    @staticmethod
    def create_analysed_document(original_filename, sentences, owner):
        from core.tasks import process_document_task

        d = Document(owner=owner,
                     original_name=original_filename,
                     title=original_filename,
                     docx_s3=None,
                     pdf_s3=None,
                     pending=True)
        d.init(sentences)
        d.save()

        process_document_task(d.pk, False, False, True)
        d = Document.objects.get(pk=d.pk)
        return d

    @staticmethod
    def make_paid(user):
        PurchasedSubscription.purchase_subscription(user, YearlyPaidSubscription)
