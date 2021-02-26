from time import sleep

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Document, Sentence, SentenceLock

SentenceLockException = SentenceLock.SentenceLockException


class SentenceLocksTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(SentenceLocksTest, cls).setUpClass()

        cls.user1 = User.objects.create(username='Tester', email='tester1@gmail.com')
        cls.user2 = User.objects.create(username='Tester 2', email='tester2@gmail.com')
        dt = Document.GENERIC

        cls.sents = ['Neither party will be responsible.',
                     'The roses are red between Company and You.',
                     'The violets are blue between Company and You.',
                     ''] # analyser also adds an empty sent at the end. Why?
        cls.repl_sent = 'Either party will be responsible.'
        cls.d = Document.objects.create(original_name='Magic Doc',
                                        title='Title', agreement_type=dt,
                                        owner=cls.user1)
        cls.d.init(cls.sents, None, None)
        cls.d.analyse()
        cls.d.save()

    @classmethod
    def tearDownClass(cls):
        cls.user2.delete()
        cls.user1.delete()

        super(SentenceLocksTest, cls).tearDownClass()

    def get_sentence(self, s_idx):
        spk = self.d.sentences_pks[s_idx]
        return Sentence.objects.get(pk=spk)

    def test_lock_attributes(self):
        # attribute of the test. how long will the lock live for
        lifetime_minutes = 0.1
        # create the lock and test default attributes
        l = SentenceLock(owner=self.user1, lifetime=lifetime_minutes)
        self.assertEqual(l.owner, self.user1)

        # test that the lock.created attribute is a time that makes sense
        time_since_created = timezone.now() - l.created
        # I assume this won't take more than 1 second to compute...
        self.assertLessEqual(time_since_created.seconds, 1)

        # test that the lock expiry works
        lock_lifetime = timezone.timedelta(minutes=l.lifetime)
        time_when_expires = l.created + lock_lifetime
        seconds_until_expiry = (time_when_expires - timezone.now()).seconds
        self.assertLessEqual(seconds_until_expiry, 60*lifetime_minutes)
        self.assertFalse(l.is_expired) # not expired yet
        # sleep for the rest of the lock's life
        sleep(lifetime_minutes*60 + 1)
        self.assertTrue(l.is_expired) # should be expired

    def test_acquire_and_release_lock(self):
        s = self.get_sentence(0)
        self.assertFalse(s.is_locked)
        self.assertIsNone(s.lock_owner)

        s.acquire_lock(self.user1)
        self.assertTrue(s.is_locked)
        self.assertEqual(s.lock_owner, self.user1)

        s.release_lock()
        self.assertFalse(s.is_locked)
        self.assertIsNone(s.lock_owner)

    def test_acquire_modify_release_lock(self):
        s = self.get_sentence(0)
        self.assertFalse(s.is_locked)
        self.assertIsNone(s.lock_owner)

        s.acquire_lock(self.user1)
        self.assertTrue(s.is_locked)
        self.assertEqual(s.lock_owner, self.user1)

        smod = s.new_revision(self.user1, text='Sentency sentence.')
        self.assertTrue(smod.is_locked)
        self.assertEqual(smod.lock_owner, self.user1)

        smod.release_lock()
        self.assertFalse(smod.is_locked)
        self.assertIsNone(smod.lock_owner)

    def test_compete_for_lock(self):
        s = self.get_sentence(0)
        self.assertFalse(s.is_locked)
        self.assertIsNone(s.lock_owner)

        s.acquire_lock(self.user1)
        with self.assertRaises(SentenceLockException):
            s.acquire_lock(self.user2)

        self.assertTrue(s.is_locked)
        self.assertEqual(s.lock_owner, self.user1)

    def test_silly_release_lock(self):
        s = self.get_sentence(0)
        self.assertFalse(s.is_locked)
        with self.assertRaises(SentenceLockException):
            s.release_lock()
        self.assertFalse(s.is_locked)
        self.assertIsNone(s.lock_owner)

    def test_lock_expires(self):
        s = self.get_sentence(0)
        self.assertFalse(s.is_locked)
        lifetime_minutes = 0.1 # this lock has a short lifetime
        s.acquire_lock(self.user1, lifetime=lifetime_minutes)
        self.assertTrue(s.is_locked)
        self.assertEqual(s.lock_owner, self.user1)
        sleep(lifetime_minutes * 60 + 1) # convert to seconds and add one
        self.assertFalse(s.is_locked)
        self.assertIsNone(s.lock_owner)
