import mock
#from urllib.parse import urlencode
import urllib

# App
from core.models import (
    DatasetCollaborationInvite,
    DatasetExternalInvite,
)
from core.tasks import (
    send_dataset_collaboration_invite_email,
    send_dataset_external_invite_email,
)
from core.utils import user_to_dict
from dataset.models import Dataset

# Django
from django.contrib.auth.models import User

# REST framework
from rest_framework.test import APITestCase


class LoggedInUserTestCaseBase(APITestCase):

    def setUp(self):
        super(LoggedInUserTestCaseBase, self).setUp()

        self.username = 'spot'
        self.email = 'spot@test.com'
        self.password = 'Spot-2017'

        self.user = User.objects.create(username=self.username,
                                        email=self.email)
        self.user.set_password(self.password)
        self.user.save()

        self.client.login(username=self.username, password=self.password)

        self.user.refresh_from_db()


class DatasetViewSetTest(LoggedInUserTestCaseBase):

    def setUp(self):
        super(DatasetViewSetTest, self).setUp()

        self.dataset = Dataset.objects.create(name='dataset_view_set_test',
                                              owner=self.user)

    def get_url(self, method=''):
        if method:
            method += '/'
        return '/api/v1/dataset/%d/%s' % (self.dataset.pk, method)

    def test_list_collaborators(self):
        user_x = User(username='user-x', email='user.x@test.com')
        user_y = User(username='user-y', email='user.y@test.com')
        user_z = User(username='user-z', email='user.z@test.com')

        user_z.save()
        DatasetCollaborationInvite.objects.create(
            invitee=user_z, inviter=self.user, dataset=self.dataset
        )

        user_y.save()
        DatasetCollaborationInvite.objects.create(
            invitee=user_y, inviter=self.user, dataset=self.dataset
        )

        # Invite user_x to join Spot
        DatasetExternalInvite.objects.create(
            email=user_x.email, inviter=self.user, dataset=self.dataset
        )

        response = self.client.get(self.get_url('list_collaborators'))
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        expected_data = {
            'pending_invites': [user_x.email],
            'collaborators': [user_to_dict(user_y), user_to_dict(user_z)]
        }
        self.assertEqual(expected_data, actual_data)

        # Suppose that user_x has just been registered, thus his/her external
        # invite should have already been converted to a collaboration invite
        user_x.save()

        response = self.client.get(self.get_url('list_collaborators'))
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        expected_data = {
            'pending_invites': [],
            'collaborators': [user_to_dict(user_x)] +
                             [user_to_dict(user_y), user_to_dict(user_z)]
        }
        self.assertEqual(expected_data, actual_data)

    @mock.patch.object(send_dataset_collaboration_invite_email, 'delay')
    @mock.patch.object(send_dataset_external_invite_email, 'delay')
    def test_invite_collaborator(self, send_external_invite_email_mock,
                                 send_collaboration_invite_email_mock):
        user = User(username='user', email='user@test.com')

        # Initial external invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(200, response.status_code)
        send_external_invite_email_mock.assert_called_once()

        DatasetExternalInvite.objects.get(
            email=user.email, inviter=self.user, dataset=self.dataset
        )

        # Duplicate external invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(400, response.status_code)

        user.save()

        # The external invite has already been transformed to the appropriate
        # collaboration invite, so delete it for further testing
        DatasetCollaborationInvite.objects.get(
            invitee=user, inviter=self.user, dataset=self.dataset
        ).delete()

        # Initial collaboration invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(200, response.status_code)
        send_collaboration_invite_email_mock.assert_called_once()

        DatasetCollaborationInvite.objects.get(
            invitee=user, inviter=self.user, dataset=self.dataset
        )

        # Duplicate collaboration invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(400, response.status_code)

    def test_uninvite_collaborator(self):
        user = User.objects.create(username='user')

        DatasetCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, dataset=self.dataset
        )

        # The owner revokes the collaborator's invitation
        response = self.client.post(self.get_url('uninvite_collaborator'),
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            DatasetCollaborationInvite.objects.filter(
                invitee=user, dataset=self.dataset
            ).exists()
        )

        DatasetCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, dataset=self.dataset
        )

        self.client.force_authenticate(user=user)

        # The collaborator revokes his/her invitation
        response = self.client.post(self.get_url('uninvite_collaborator'))
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            DatasetCollaborationInvite.objects.filter(
                invitee=user, dataset=self.dataset
            ).exists()
        )

    def test_user_collaboration_management_access(self):
        user = User.objects.create(username='user')

        # The dataset isn't accessible for unauthenticated users
        # and isn't visible for non-collaborators

        self.client.force_authenticate(user=None)

        response = self.client.get(self.get_url())
        self.assertEqual(403, response.status_code)

        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_url())
        self.assertEqual(404, response.status_code)

        # Though even for collaborators some endpoints aren't permitted

        DatasetCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, dataset=self.dataset
        )

        response = self.client.get(self.get_url('list_collaborators'))
        self.assertEqual(403, response.status_code)

        response = self.client.post(self.get_url('invite_collaborator'))
        self.assertEqual(403, response.status_code)

        # The collaborator can only revoke his/her invitation

        response = self.client.post(self.get_url('uninvite_collaborator'),
                                    {'username': self.username}, format='json')
        self.assertEqual(403, response.status_code)  # FAILED

        response = self.client.post(self.get_url('uninvite_collaborator'),
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)  # OK

        self.assertFalse(
            DatasetCollaborationInvite.objects.filter(
                invitee=user, dataset=self.dataset
            ).exists()
        )

    def test_allowed_users(self):
        # The dataset isn't accessible for unauthenticated users
        self.client.force_authenticate(user=None)
        response = self.client.get(self.get_url('allowed_users'))
        self.assertEqual(403, response.status_code)

        user_x = User(username='user-x', email='user.x@test.com')
        user_y = User(username='user-y', email='user.y@test.com')
        user_z = User(username='user-z', email='user.z@test.com')

        user_z.save()
        DatasetCollaborationInvite.objects.create(
            invitee=user_z, inviter=self.user, dataset=self.dataset
        )

        user_y.save()
        DatasetCollaborationInvite.objects.create(
            invitee=user_y, inviter=self.user, dataset=self.dataset
        )

        # Invite user_x to join Spot
        DatasetExternalInvite.objects.create(
            email=user_x.email, inviter=self.user, dataset=self.dataset
        )

        expected_data = list(map(user_to_dict, [self.user, user_y, user_z]))

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url('allowed_users'))
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        self.assertEqual(expected_data, actual_data)

        # The other collaborators should see the same result as the owner
        for user in [user_y, user_z]:
            self.client.force_authenticate(user=user)
            response = self.client.get(self.get_url('allowed_users'))
            self.assertEqual(200, response.status_code)
            actual_data = response.json()
            self.assertEqual(expected_data, actual_data)

        # Suppose that user_x has just been registered, thus his/her external
        # invite should have already been converted to a collaboration invite
        user_x.save()

        expected_data = list(map(user_to_dict, [self.user, user_x, user_y, user_z]))

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url('allowed_users'))
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        self.assertEqual(expected_data, actual_data)

        # The other collaborators should see the same result as the owner
        for user in [user_x, user_y, user_z]:
            self.client.force_authenticate(user=user)
            response = self.client.get(self.get_url('allowed_users'))
            self.assertEqual(200, response.status_code)
            actual_data = response.json()
            self.assertEqual(expected_data, actual_data)

        # Revoke access to the dataset from user_x
        DatasetCollaborationInvite.objects.filter(
            invitee=user_x, dataset=self.dataset
        ).delete()

        # The dataset isn't visible for non-collaborators
        self.client.force_authenticate(user=user_x)
        response = self.client.get(self.get_url('allowed_users'))
        self.assertEqual(404, response.status_code)


class SampleViewSetTest(LoggedInUserTestCaseBase):

    def setUp(self):
        super(SampleViewSetTest, self).setUp()

        self.dataset = Dataset.objects.create(
            name='sample_view_set_test',
            klasses=['consonant', 'vowel'],
            samples={
                'texts': ['A', 'B', 'C', 'D', 'E'],
                'labels': [1, 0, 0, 0, 1]
            },
            owner=self.user
        )

    def get_url(self, sample_index=None, dataset_pk=None, query_params=None):
        if dataset_pk is None:
            dataset_pk = self.dataset.pk
        url = '/api/v1/dataset/%s/sample/' % dataset_pk
        if sample_index is not None:
            url += '%s/' % sample_index
        if query_params is not None:
            url += '?' + urllib.parse.urlencode(query_params, doseq=True)
        return url

    @property
    def texts(self):
        return self.dataset.texts

    @property
    def index_labels(self):
        return self.dataset.index_labels

    @property
    def klass_labels(self):
        return self.dataset.klass_labels

    @property
    def samples_count(self):
        return self.dataset.samples_count

    def get_sample(self, sample_index):
        return {
            'text': self.texts[sample_index],
            'label': self.klass_labels[sample_index],
            'dataset': self.dataset.pk,
            'index': sample_index
        }

    def form_sample(self, text, label, sample_index=None):
        if sample_index is None:
            sample_index = self.samples_count
        return {
            'text': text,
            'label': label,
            'dataset': self.dataset.pk,
            'index': sample_index
        }

    # Actual test methods

    def test_dataset_not_found(self):
        invalid_dataset_pk = self.dataset.pk - 1
        response = self.client.get(self.get_url(dataset_pk=invalid_dataset_pk))
        self.assertEqual(404, response.status_code)

        invalid_dataset_pk = self.dataset.pk + 1
        response = self.client.get(self.get_url(dataset_pk=invalid_dataset_pk))
        self.assertEqual(404, response.status_code)

    def test_sample_not_found(self):
        invalid_sample_index = -1
        response = self.client.get(self.get_url(invalid_sample_index))
        self.assertEqual(404, response.status_code)

        invalid_sample_index = self.samples_count
        response = self.client.get(self.get_url(invalid_sample_index))
        self.assertEqual(404, response.status_code)

    def test_retrieve(self):
        sample_index = 2
        expected_sample = self.get_sample(sample_index)
        response = self.client.get(self.get_url(sample_index))
        self.assertEqual(200, response.status_code)
        actual_sample = response.json()
        self.assertEqual(expected_sample, actual_sample)

    def test_update(self):
        sample_index = 2
        expected_sample = self.form_sample(text='F', label='consonant',
                                           sample_index=sample_index)
        response = self.client.put(self.get_url(sample_index),
                                   expected_sample, format='json')
        self.assertEqual(200, response.status_code)
        actual_sample = response.json()
        self.assertEqual(expected_sample, actual_sample)
        # Check whether the sample was actually updated in the db
        self.dataset.refresh_from_db()
        expected_sample = self.get_sample(sample_index)
        self.assertEqual(expected_sample, actual_sample)

    def test_invalid_update(self):
        sample_index = 2
        expected_sample = self.form_sample(text='F', label='invalid',
                                           sample_index=sample_index)
        response = self.client.put(self.get_url(sample_index),
                                   expected_sample, format='json')
        self.assertEqual(400, response.status_code)

    def test_partial_update(self):
        sample_index = 2
        # Update the text, but don't update the label
        expected_sample = self.get_sample(sample_index)
        expected_sample['text'] = 'F'
        expected_partial_sample = expected_sample.copy()
        del expected_partial_sample['label']
        response = self.client.patch(self.get_url(sample_index),
                                     expected_partial_sample, format='json')
        self.assertEqual(200, response.status_code)
        actual_sample = response.json()
        self.assertEqual(expected_sample, actual_sample)
        # Check whether the sample was actually updated in the db
        self.dataset.refresh_from_db()
        expected_sample = self.get_sample(sample_index)
        self.assertEqual(expected_sample, actual_sample)

    def test_invalid_partial_update(self):
        sample_index = 2
        # Don't update the text, but try to update the label
        expected_sample = self.get_sample(sample_index)
        expected_sample['label'] = 'invalid'
        expected_partial_sample = expected_sample.copy()
        del expected_partial_sample['text']
        response = self.client.patch(self.get_url(sample_index),
                                     expected_partial_sample, format='json')
        self.assertEqual(400, response.status_code)

    def test_list(self):
        expected_samples = [self.get_sample(sample_index)
                            for sample_index in range(self.samples_count)]
        response = self.client.get(self.get_url())
        self.assertEqual(200, response.status_code)
        # All the samples should fit into a single page
        payload = response.json()
        self.assertEqual(self.samples_count, payload['count'])
        actual_samples = payload['results']
        self.assertEqual(expected_samples, actual_samples)

    def test_list_filtering(self):
        samples = [self.get_sample(sample_index)
                   for sample_index in range(self.samples_count)]

        # Test filtering by both single label and multiple labels
        for labels in ['unknown', 'consonant', 'vowel',
                       ['unknown', 'consonant', 'vowel']]:
            if not isinstance(labels, list):
                labels = [labels]
            expected_samples = [sample for sample in samples
                                if sample['label'] in labels]
            response = self.client.get(
                self.get_url(query_params={'label': labels})
            )
            self.assertEqual(200, response.status_code)
            # All the samples should fit into a single page
            payload = response.json()
            self.assertEqual(len(expected_samples), payload['count'])
            actual_samples = payload['results']
            self.assertEqual(expected_samples, actual_samples)

        # Test filtering by text snippet
        for search, found in \
                [('C', True), ('c', True), ('F', False), ('f', False)]:
            expected_samples = [sample for sample in samples
                                if sample['text'] == search.upper()]
            self.assertEqual(found, bool(expected_samples))
            response = self.client.get(
                self.get_url(query_params={'search': search})
            )
            self.assertEqual(200, response.status_code)
            # All the samples should fit into a single page
            payload = response.json()
            self.assertEqual(len(expected_samples), payload['count'])
            actual_samples = payload['results']
            self.assertEqual(expected_samples, actual_samples)

    def test_list_sorting(self):
        samples = [self.get_sample(sample_index)
                   for sample_index in range(self.samples_count)]

        # Test sorting by body/text/label in invalid/asc/desc order
        for sort_by in ('body', 'text', 'label'):
            for order in ('invalid', 'asc', 'desc'):
                query_params = {'sortBy': sort_by,
                                'order': order}
                if sort_by == 'body':  # alias
                    sort_by = 'text'
                sort_params = {'key': lambda sample: sample[sort_by],
                               'reverse': order == 'desc'}
                expected_samples = sorted(samples, **sort_params)
                response = self.client.get(
                    self.get_url(query_params=query_params)
                )
                self.assertEqual(200, response.status_code)
                # All the samples should fit into a single page
                payload = response.json()
                self.assertEqual(len(expected_samples), payload['count'])
                actual_samples = payload['results']
                self.assertEqual(expected_samples, actual_samples)

    def test_create(self):
        expected_sample = self.form_sample(text='F', label='consonant')
        response = self.client.post(self.get_url(),
                                    expected_sample, form='json')
        self.assertEqual(200, response.status_code)
        actual_sample = response.json()
        self.assertEqual(expected_sample, actual_sample)
        # Check whether the sample was actually created in the db
        old_samples_count = self.samples_count
        self.dataset.refresh_from_db()
        new_samples_count = self.samples_count
        self.assertEqual(old_samples_count + 1, new_samples_count)
        expected_sample = self.get_sample(old_samples_count)
        self.assertEqual(expected_sample, actual_sample)

    def test_invalid_create(self):
        expected_sample = self.form_sample(text='F', label='invalid')
        response = self.client.post(self.get_url(),
                                    expected_sample, form='json')
        self.assertEqual(400, response.status_code)

    def test_destroy(self):
        sample_index = 2
        expected_sample = self.get_sample(sample_index)
        response = self.client.delete(self.get_url(sample_index))
        self.assertEqual(200, response.status_code)
        actual_sample = response.json()
        self.assertEqual(expected_sample, actual_sample)
        # Check whether the sample was actually deleted from the db
        old_samples_count = self.samples_count
        self.dataset.refresh_from_db()
        new_samples_count = self.samples_count
        self.assertEqual(old_samples_count - 1, new_samples_count)

    def test_user_access(self):
        url = self.get_url()

        self.client.force_authenticate(user=self.user)

        response = self.client.get(url)
        # Owner: OK
        self.assertEqual(200, response.status_code)

        self.client.force_authenticate(user=None)

        response = self.client.get(url)
        # Unauthenticated: FAILED
        self.assertEqual(403, response.status_code)

        user = User.objects.create(username='user')

        self.client.force_authenticate(user=user)

        response = self.client.get(url)
        # Authenticated, but neither owner nor collaborator (yet): FAILED
        self.assertEqual(404, response.status_code)

        DatasetCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, dataset=self.dataset
        )

        response = self.client.get(url)
        # Collaborator: OK
        self.assertEqual(200, response.status_code)
