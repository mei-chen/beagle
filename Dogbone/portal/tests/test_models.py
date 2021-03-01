from django.test import TestCase
from django.contrib.auth.models import User

from portal.models import UserProfile, PDFUploadMonitor
from django.forms import ValidationError


class UserTestCase(TestCase):

    def test_profile_create(self):
        self.assertEqual(len(User.objects.all()), 0)
        self.assertEqual(len(UserProfile.objects.all()), 0)

        u = User(username='username')
        u.set_password('aaaa')
        u.save()

        self.assertEqual(len(User.objects.all()), 1)
        self.assertEqual(len(UserProfile.objects.all()), 1)

        u = User.objects.get(username='username')
        self.assertIsNotNone(u.details)

    def test_profile_delete(self):
        self.assertEqual(len(User.objects.all()), 0)
        self.assertEqual(len(UserProfile.objects.all()), 0)

        u = User(username='username')
        u.set_password('aaaa')
        u.save()

        u = User.objects.get(username='username')
        self.assertIsNotNone(u.details)

        u.delete()
        self.assertEqual(len(User.objects.all()), 0)
        self.assertEqual(len(UserProfile.objects.all()), 0)

    def test_unique_email_create_exception(self):
        User.objects.create_user('user1', 'mail@email.com', 'p@ss')
        self.assertRaises(ValidationError, User.objects.create_user, 'user2', 'mail@email.com', 'p@ss')

    def test_unique_email_update_exception(self):
        User.objects.create_user('user1', 'mail@email.com', 'p@ss')
        u = User.objects.create_user('user2', 'other@email.com', 'p@ss')

        u.email = 'mail@email.com'
        self.assertRaises(ValidationError, u.save)

    def test_unique_email_not_checking_itself(self):
        u = User.objects.create_user('user', 'mail@email.com', 'p@ss')
        u.username = 'other'

        try:
            u.save()
        except ValidationError:
            self.assertTrue(False, msg="While trying to update, the model took itself into consideration")

    def test_lowercase_email(self):
        u = User.objects.create_user('user', 'Mail@email.cOM', 'p@ss')
        self.assertEqual(u.email, 'mail@email.com')
        self.assertIsNotNone(User.objects.get(email='mail@email.com'))


class PDFMonitorTestCase(TestCase):

    def test_basic_add_counts(self):
        self.assertEqual(len(PDFUploadMonitor.objects.all()), 0)

        stat = PDFUploadMonitor()
        stat.save()

        self.assertEqual(len(PDFUploadMonitor.objects.all()), 1)

        stat = PDFUploadMonitor.objects.latest()
        self.assertIsNotNone(stat.docs)

        stat.add_doc(pages=10)
        self.assertEqual(stat.docs,  1)
        self.assertEqual(stat.pages, 10)
        self.assertEqual(stat.docs_ocred,  0)
        self.assertEqual(stat.pages_ocred, 0)

    def test_new_month(self):
        from datetime import date

        old_stat = PDFUploadMonitor()
        old_stat.startdate = date(1990, 3, 8)
        old_stat.save()

        self.assertEqual(len(PDFUploadMonitor.objects.all()), 1)

        stat = PDFUploadMonitor.objects.latest()
        self.assertIsNotNone(stat.docs)

        stat.add_doc(pages=10, ocr=True)
        # The old one should be on 0 still (as a new month has been created)
        self.assertEqual(stat.docs,  0)
        self.assertEqual(stat.pages, 0)
        self.assertEqual(stat.docs_ocred,  0)
        self.assertEqual(stat.pages_ocred, 0)

        stat = PDFUploadMonitor.objects.latest()
        self.assertEqual(stat.docs,  0)
        self.assertEqual(stat.pages, 0)
        self.assertEqual(stat.docs_ocred,  1)
        self.assertEqual(stat.pages_ocred, 10)
