import json
import mock
import re
import uuid

# Django
from django.contrib.auth.models import User
from django.test import TestCase

# REST framework
from rest_framework.test import APITestCase

# NumPy
import numpy as np

# App
from core.models import (
    ExperimentCollaborationInvite,
    ExperimentExternalInvite,
)
from core.tasks import (
    send_experiment_collaboration_invite_email,
    send_experiment_external_invite_email,
)
from core.utils import user_to_dict
from dataset.models import (
    Dataset,
    DatasetMapping,
)
from experiment.models import (
    Formula,
    DEFAULT_EXPERIMENT_NAME,
    default_experiment_name_re,
    Experiment,
    RegexClassifier,
    BuiltInClassifier,
    TrainedClassifier,
)
from experiment.tasks import (
    simulate_classification,
    evaluate_metrics,
    generate_predictions,
)
from realtime.notify import NotificationManager


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


class ValidateRegexTest(LoggedInUserTestCaseBase):

    def test_call_validate_regex_no_regex(self):
        response = self.client.post('/api/v1/validate_regex')
        self.assertEqual(
            {'error': 'Please pass a regex string'},
            json.loads(response.content)
        )

    def test_call_validate_regex_invalid_regex(self):
        body = {
            'regex': 'abc['
        }
        response = self.client.post('/api/v1/validate_regex',
                                    json.dumps(body),
                                    content_type='application/json')
        self.assertEqual(
            {'regex_is_valid': False,
             'error': 'unexpected end of regular expression'},
            json.loads(response.content)
        )

    def test_call_validate_regex_valid(self):
        body = {
            'regex': r'(?<=id\d:)(\b\w*\b)'
        }
        response = self.client.post('/api/v1/validate_regex',
                                    json.dumps(body),
                                    content_type='application/json')
        self.assertEqual(
            {'regex_is_valid': True},
            json.loads(response.content)
        )


class ExperimentViewSetTest(LoggedInUserTestCaseBase):

    def setUp(self):
        super(ExperimentViewSetTest, self).setUp()

        self.request_data = {
            'name': 'qwerty',
            'formula': [
                {
                    'weight': 0.6,
                    'classifier': {'type': 'regex', 'apply': 'include',
                                   'name': '+a', 'expression': 'a+'}
                },
                {
                    'weight': 0.3,
                    'classifier': {'type': 'regex', 'apply': 'exclude',
                                   'name': '-b', 'expression': 'b+'}
                },
                {
                    'weight': 0.1,
                    'classifier': {'type': 'regex', 'apply': 'include',
                                   'name': '+c', 'expression': 'c+'}
                }
            ]
        }

        self.experiment = Experiment.objects.create(
            name='experiment_view_set_test', owner=self.user
        )

    def test_create(self):
        response = self.client.post('/api/v1/experiment/', self.request_data,
                                    format='json')
        response_data = response.json()

        self.assertIsInstance(response_data['id'], int)
        self.assertEqual(self.request_data['name'], response_data['name'])

        request_formula = self.request_data['formula']
        response_formula = response_data['formula']['content']
        self.assertEqual(len(request_formula), len(response_formula))

        for request_clf_data, response_clf_data in \
                zip(request_formula, response_formula):
            # UUIDs of the requested classifiers must be added to the response
            del response_clf_data['uuid']
            self.assertEqual(request_clf_data, response_clf_data)

    def mock_clf_results(self, name, weight, status=False, sample=None,
                         clf_type='regex'):
        clf_results = {
            'name': name,
            'type': clf_type,
            'uuid': mock.ANY,
            'weight': self.mock_number(weight),
            'status': status
        }
        if sample is not None:
            clf_results['sample'] = [(token, self.mock_number(score))
                                     for token, score in sample]
        return clf_results

    @mock.patch.object(simulate_classification, 'delay',
                       side_effect=simulate_classification)
    @mock.patch.object(NotificationManager, 'notify_client')
    def test_simulate(self, notify_client_mock,
                      simulate_classification_delay_mock):
        # Create an experiment and use its ID for simulations
        request_url = '/api/v1/experiment/'
        response = self.client.post(request_url, self.request_data,
                                    format='json')
        response_data = response.json()
        experiment_pk = response_data['id']
        request_url += '%d/simulate/' % experiment_pk

        session_key = mock.ANY
        task_uuid = str(uuid.uuid4())

        # Consider all but empty combinations of {'a', 'bb', 'ccc'}

        self.client.post(request_url,
                         {'sample': 'a', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='a', task_uuid=task_uuid
        )
        self.assertEqual(1, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': True,
                'confidence': self.mock_number(0.8),
                'sample': [('a', self.mock_number(1.0))]
            },
            'results_per_classifier': [
                self.mock_clf_results('+a', 0.6, True, [('a', 1.0)]),
                self.mock_clf_results('-b', 0.3, True, [('a', 1.0)]),
                self.mock_clf_results('+c', 0.1, False)
            ]
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(1, notify_client_mock.call_count)

        self.client.post(request_url,
                         {'sample': 'bb', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='bb', task_uuid=task_uuid
        )
        self.assertEqual(2, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': False,
                'confidence': self.mock_number(1.0)
            }
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(2, notify_client_mock.call_count)

        self.client.post(request_url,
                         {'sample': 'ccc', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='ccc', task_uuid=task_uuid
        )
        self.assertEqual(3, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': False,
                'confidence': self.mock_number(0.2),
                'sample': [('ccc', self.mock_number(1.0))]
            },
            'results_per_classifier': [
                self.mock_clf_results('+a', 0.6, False),
                self.mock_clf_results('-b', 0.3, True, [('ccc', 1.0)]),
                self.mock_clf_results('+c', 0.1, True, [('ccc', 1.0)])
            ]
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(3, notify_client_mock.call_count)

        self.client.post(request_url,
                         {'sample': 'a bb', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='a bb', task_uuid=task_uuid
        )
        self.assertEqual(4, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': True,
                'confidence': self.mock_number(0.2),
                'sample': [('a', self.mock_number(1.0)),
                           ('bb', self.mock_number(0.3333333333))]
            },
            'results_per_classifier': [
                self.mock_clf_results('+a', 0.6, True, [('a', 1.0),
                                                        ('bb', 0.0)]),
                self.mock_clf_results('-b', 0.3, False),
                self.mock_clf_results('+c', 0.1, False)
            ]
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(4, notify_client_mock.call_count)

        self.client.post(request_url,
                         {'sample': 'bb ccc', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='bb ccc', task_uuid=task_uuid
        )
        self.assertEqual(5, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': False,
                'confidence': self.mock_number(0.8),
                'sample': [('bb', self.mock_number(1.0)),
                           ('ccc', self.mock_number(1.0))]
            },
            'results_per_classifier': [
                self.mock_clf_results('+a', 0.6, False),
                self.mock_clf_results('-b', 0.3, False),
                self.mock_clf_results('+c', 0.1, True, [('bb', 0.0),
                                                        ('ccc', 1.0)])
            ]
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(5, notify_client_mock.call_count)

        self.client.post(request_url,
                         {'sample': 'a ccc', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='a ccc', task_uuid=task_uuid
        )
        self.assertEqual(6, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': True,
                'confidence': self.mock_number(1.0),
                'sample': [('a', self.mock_number(1.0)),
                           ('ccc', self.mock_number(0.3333333333))]
            },
             'results_per_classifier': [
                self.mock_clf_results('+a', 0.6, True, [('a', 1.0),
                                                        ('ccc', 0.0)]),
                self.mock_clf_results('-b', 0.3, True, [('a', 1.0),
                                                        ('ccc', 1.0)]),
                self.mock_clf_results('+c', 0.1, True, [('a', 0.0),
                                                        ('ccc', 1.0)])
            ]
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(6, notify_client_mock.call_count)

        self.client.post(request_url,
                         {'sample': 'a bb ccc', 'task_uuid': task_uuid},
                         format='json')
        simulate_classification_delay_mock.assert_called_with(
            session_key=session_key, experiment_pk=experiment_pk,
            sample='a bb ccc', task_uuid=task_uuid
        )
        self.assertEqual(7, simulate_classification_delay_mock.call_count)
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
            'results': {
                'status': True,
                'confidence': self.mock_number(0.4),
                'sample': [('a', self.mock_number(1.0)),
                           ('bb', self.mock_number(0.4545454545)),
                           ('ccc', self.mock_number(0.1818181818))]
            },
            'results_per_classifier': [
                self.mock_clf_results('+a', 0.6, True, [('a', 1.0),
                                                        ('bb', 0.0),
                                                        ('ccc', 0.0)]),
                self.mock_clf_results('-b', 0.3, False),
                self.mock_clf_results('+c', 0.1, True, [('a', 0.0),
                                                        ('bb', 0.0),
                                                        ('ccc', 1.0)])
            ]
        }
        notify_client_mock.assert_called_with(session_key, payload)
        self.assertEqual(7, notify_client_mock.call_count)

    def test_get_set_evaluate_data(self):
        experiment_pk = self.experiment.pk
        dataset_pk = 12345  # not necessarily valid
        mapping = {'neg': ['a', 'b', 'c'], 'pos': ['d', 'e', 'f']}

        url_template = '/api/v1/experiment/%d/%s_evaluate_data/'
        get_url = url_template % (experiment_pk, 'get')
        set_url = url_template % (experiment_pk, 'set')

        # get before set
        response = self.client.get(get_url)
        self.assertEqual(404, response.status_code)

        # set
        data = {'id': dataset_pk, 'mapping': mapping}
        response = self.client.post(set_url, data, format='json')
        self.assertEqual(200, response.status_code)

        # get after set
        response = self.client.get(get_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), data)

    @staticmethod
    def mock_number(number):
        number_mock = mock.MagicMock()
        number_mock.value = number
        # Make comparison of floating-point numbers more robust
        number_mock.__eq__ = lambda self, other: np.isclose(self.value, other)
        return number_mock

    @mock.patch.object(NotificationManager, 'notify_client')
    def test_evaluate(self, notify_client_mock):
        session_key = 'experiment_view_set_test_session_key'
        task_uuid = str(uuid.uuid4())

        formula = Formula.objects.create()
        formula.create_classifiers([
            {
                'weight': 1.0,
                'classifier': {'type': 'regex', 'apply': 'include',
                               'expression': 'n|N'}
            }
        ])
        experiment = Experiment.objects.create(
            name='experiment_view_set_test_experiment',
            formula=formula
        )

        dataset = Dataset.objects.create(
            name='experiment_view_set_test_dataset',
            klasses=['Africa', 'Asia', 'Europe'],
            samples={
                'texts': ['Senegal', 'Ukraine', 'China',
                          'Egypt', 'Romania', 'India'],
                'labels': [0, 2, 1, 0, 2, 1]
            }
        )

        mapping = {'neg': ['Asia', 'Europe'], 'pos': ['Africa']}

        # Thus in the modeled experiment we believe, that a country from
        # the dataset is located in Africa, if its name contains the letters
        # 'n' or 'N' at least once (not very realistic though, but our aim here
        # is to obtain as many types of binary matches/mismatches as possible)

        self.assertTrue(
            evaluate_metrics(session_key, experiment.pk, dataset.pk,
                             mapping, False, task_uuid)
        )

        precision = 0.2
        recall = 0.5
        f1 = 2 * (precision * recall) / (precision + recall)

        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_EVALUATED_NOTIFICATION,
            'scores': {
                'precision': self.mock_number(precision),
                'recall': self.mock_number(recall),
                'f1': self.mock_number(f1)
            }
        }

        notify_client_mock.assert_called_once_with(session_key, payload)

    @staticmethod
    def mock_uuid():
        uuid_mock = mock.MagicMock()
        uuid_mock.uuid_re = re.compile(r'^[a-z0-9\-]+$')
        uuid_mock.__eq__ = lambda self, other: bool(self.uuid_re.match(other))
        return uuid_mock

    @mock.patch.object(NotificationManager, 'notify_client')
    def test_generate(self, notify_client_mock):
        session_key = 'experiment_view_set_test_session_key'
        task_uuid = str(uuid.uuid4())

        formula = Formula.objects.create()
        formula.create_classifiers([
            {
                'weight': 1.0,
                'classifier': {'type': 'regex', 'apply': 'include',
                               'expression': '[Ee]g'}
            }
        ])
        experiment = Experiment.objects.create(
            name='experiment_view_set_test_experiment',
            formula=formula
        )

        dataset = Dataset.objects.create(
            name='experiment_view_set_test_dataset',
            klasses=['Africa', 'Asia', 'Europe'],
            samples={
                'texts': ['Senegal', 'Ukraine', 'China',
                          'Egypt', 'Romania', 'India'],
                'labels': [0, 2, 1, 0, 2, 1]
            }
        )

        mapping = {'neg': ['Asia', 'Europe'], 'pos': ['Africa']}

        # Thus the modeled experiment selects a country from the dataset,
        # if its name contains the combinations of letters
        # either 'Eg' or 'eg' at least once

        self.assertTrue(
            generate_predictions(session_key, experiment.pk, dataset.pk,
                                 mapping, False, task_uuid)
        )

        preview = {
            'results': [
                {'text': 'Senegal', 'label': True},
                {'text': 'Ukraine', 'label': False},
                {'text': 'China', 'label': False},
                {'text': 'Egypt', 'label': True},
                {'text': 'Romania', 'label': False},
                {'text': 'India', 'label': False}
            ],
            'stats': {
                'positive': 2,
                'negative': 4,
                'total': 6
            }
        }

        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_GENERATED_NOTIFICATION,
            'preview': preview
        }

        notify_client_mock.assert_called_once_with(session_key, payload)

        # Check that the predictions were actually stored in the cache

        self.assertEqual(
            {'dataset_pk': dataset.pk, 'mapping': mapping, 'split': False,
             'predictions': [True, False, False, True, False, False]},
            experiment.get_cached_data('generate')
        )

    def get_url(self, method=''):
        if method:
            method += '/'
        return '/api/v1/experiment/%d/%s' % (self.experiment.pk, method)

    def test_list_collaborators(self):
        user_x = User(username='user-x', email='user.x@test.com')
        user_y = User(username='user-y', email='user.y@test.com')
        user_z = User(username='user-z', email='user.z@test.com')

        user_z.save()
        ExperimentCollaborationInvite.objects.create(
            invitee=user_z, inviter=self.user, experiment=self.experiment
        )

        user_y.save()
        ExperimentCollaborationInvite.objects.create(
            invitee=user_y, inviter=self.user, experiment=self.experiment
        )

        # Invite user_x to join Spot
        ExperimentExternalInvite.objects.create(
            email=user_x.email, inviter=self.user, experiment=self.experiment
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

    @mock.patch.object(send_experiment_collaboration_invite_email, 'delay')
    @mock.patch.object(send_experiment_external_invite_email, 'delay')
    def test_invite_collaborator(self, send_external_invite_email_mock,
                                 send_collaboration_invite_email_mock):
        user = User(username='user', email='user@test.com')

        # Initial external invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(200, response.status_code)
        send_external_invite_email_mock.assert_called_once()

        ExperimentExternalInvite.objects.get(
            email=user.email, inviter=self.user, experiment=self.experiment
        )

        # Duplicate external invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(400, response.status_code)

        user.save()

        # The external invite has already been transformed to the appropriate
        # collaboration invite, so delete it for further testing
        ExperimentCollaborationInvite.objects.get(
            invitee=user, inviter=self.user, experiment=self.experiment
        ).delete()

        # Initial collaboration invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(200, response.status_code)
        send_collaboration_invite_email_mock.assert_called_once()

        ExperimentCollaborationInvite.objects.get(
            invitee=user, inviter=self.user, experiment=self.experiment
        )

        # Duplicate collaboration invitation
        response = self.client.post(self.get_url('invite_collaborator'),
                                    {'email': user.email}, format='json')
        self.assertEqual(400, response.status_code)

    def test_uninvite_collaborator(self):
        user = User.objects.create(username='user')

        ExperimentCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, experiment=self.experiment
        )

        # The owner revokes the collaborator's invitation
        response = self.client.post(self.get_url('uninvite_collaborator'),
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            ExperimentCollaborationInvite.objects.filter(
                invitee=user, experiment=self.experiment
            ).exists()
        )

        ExperimentCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, experiment=self.experiment
        )

        self.client.force_authenticate(user=user)

        # The collaborator revokes his/her invitation
        response = self.client.post(self.get_url('uninvite_collaborator'))
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            ExperimentCollaborationInvite.objects.filter(
                invitee=user, experiment=self.experiment
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

        ExperimentCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, experiment=self.experiment
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
            ExperimentCollaborationInvite.objects.filter(
                invitee=user, experiment=self.experiment
            ).exists()
        )


class FormulaTest(TestCase):

    def setUp(self):
        super(FormulaTest, self).setUp()

        self.clfs = [
            RegexClassifier(name='A', expression='a+', reverse=False),
            RegexClassifier(name='B', expression='b+', reverse=True),
            RegexClassifier(name='C', expression='c+', reverse=False),
        ]

        for clf in self.clfs:
            clf.save()

        self.formula = Formula()
        # Set null weights initially
        self.update_weights()

    def update_weights(self, weights=None):
        if weights is None:
            weights = [0] * len(self.clfs)
        self.formula.content = map(
            lambda (c, w): {'uuid': c.uuid, 'weight': w},
            zip(self.clfs, weights)
        )
        self.formula.save()

    def predict(self, text):
        prediction, confidence = self.formula.predict(
            [text], with_confidence=True
        )
        return prediction[0], confidence[0]

    @staticmethod
    def mock_number(number):
        number_mock = mock.MagicMock()
        number_mock.value = number
        # Make comparison of floating-point numbers more robust
        number_mock.__eq__ = lambda self, other: np.isclose(self.value, other)
        return number_mock

    def test_predict(self):
        prediction, confidence = self.predict('abc')
        self.assertTrue(prediction)
        self.assertEqual(self.mock_number(0.3333333333), confidence)

        self.update_weights([1] * 3)
        prediction, confidence = self.predict('abc')
        self.assertTrue(prediction)
        self.assertEqual(self.mock_number(0.3333333333), confidence)

        self.update_weights([0.25, 0.5, 0.25])
        prediction, confidence = self.predict('abc')
        self.assertFalse(prediction)
        self.assertEqual(self.mock_number(0.0), confidence)

        self.update_weights([0.3, 0.4, 0.3])
        prediction, confidence = self.predict('abc')
        self.assertTrue(prediction)
        self.assertEqual(self.mock_number(0.2), confidence)

        self.update_weights([0.2, 0.6, 0.2])
        prediction, confidence = self.predict('abc')
        self.assertFalse(prediction)
        self.assertEqual(self.mock_number(0.2), confidence)

        self.update_weights([0.0, 1.0, 0.0])
        prediction, confidence = self.predict('abc')
        self.assertFalse(prediction)
        self.assertEqual(self.mock_number(1.0), confidence)


class ExperimentTest(TestCase):

    @staticmethod
    def get_name(number=None):
        name = DEFAULT_EXPERIMENT_NAME
        if number is not None:
            name += ' %d' % number
        return name

    @staticmethod
    def get_number(name):
        number = default_experiment_name_re.match(name).group(1)
        if number is not None:
            number = int(number)
        return number

    @staticmethod
    def create_experiment(name=None, owner=None, public=True):
        return Experiment.objects.create(name=name, owner=owner, public=public)

    @staticmethod
    def create_user(username):
        return User.objects.create(username=username)

    def test_default_name_generation(self):
        experiment_0 = self.create_experiment(self.get_name(0))
        self.assertEqual(0, self.get_number(experiment_0.name))

        experiment_1 = self.create_experiment(self.get_name(1))
        self.assertEqual(1, self.get_number(experiment_1.name))

        experiment_4 = self.create_experiment(self.get_name(4))
        self.assertEqual(4, self.get_number(experiment_4.name))

        experiment = self.create_experiment()
        self.assertEqual(self.get_name(), experiment.name)
        self.assertEqual(None, self.get_number(experiment.name))

        experiment_2 = self.create_experiment()
        self.assertEqual(self.get_name(2), experiment_2.name)
        self.assertEqual(2, self.get_number(experiment_2.name))

        experiment_3 = self.create_experiment()
        self.assertEqual(self.get_name(3), experiment_3.name)
        self.assertEqual(3, self.get_number(experiment_3.name))

        experiment_5 = self.create_experiment()
        self.assertEqual(self.get_name(5), experiment_5.name)
        self.assertEqual(5, self.get_number(experiment_5.name))

    def test_defaul_name_generation_for_different_users(self):
        users = {
            1: self.create_user('Alice'),
            2: self.create_user('Bob'),
            3: self.create_user('Eve'),
        }
        actual_experiments_names = {user_id: [] for user_id in users}
        # The users are going to independently create some experiments in turn
        for _ in range(5):
            for user_id in users:
                # Create a default experiment for the given user
                experiment = self.create_experiment(owner=users[user_id])
                actual_experiments_names[user_id].append(experiment.name)
        # The generated names should be the same due to the same creation order
        # by each user, but still they should remain unique for each user
        expected_experiments_names = [self.get_name(number)
                                      for number in [None, 2, 3, 4, 5]]
        for user_id in users:
            self.assertEqual(expected_experiments_names,
                             actual_experiments_names[user_id])

    def test_default_name_generation_in_public_private_namespaces(self):
        namespaces = [True, False]
        actual_experiments_names = {namespace: [] for namespace in namespaces}
        # The namespaces are going to independently be filled with some
        # experiments in turn
        for _ in range(5):
            for namespace in namespaces:
                # Create a default experiment (without any owner) in the given
                # namespace
                experiment = self.create_experiment(public=namespace)
                actual_experiments_names[namespace].append(experiment.name)
        # The generated names should be the same due to the same filling order
        # to each namespace, but still they should remain unique within each
        # namespace
        expected_experiments_names = [self.get_name(number)
                                      for number in [None, 2, 3, 4, 5]]
        for namespace in namespaces:
            self.assertEqual(expected_experiments_names,
                             actual_experiments_names[namespace])


class GenericClassifierTest(TestCase):
    """ Abstract base class for testing different types of classifiers. """

    @classmethod
    def get_clf_class(cls):
        raise NotImplementedError

    def setUp(self):
        super(GenericClassifierTest, self).setUp()

        self.clf = self.get_clf_class().objects.create()

    # There shouldn't be any tests here!


class RegexClassifierTest(GenericClassifierTest):

    @classmethod
    def get_clf_class(cls):
        return RegexClassifier

    def test_config(self):
        self.clf.config(
            expression='\d',
            apply='exclude',
            # Some unused params (should go into kwargs)
            x=1, y=2, z=3
        )

        self.assertEqual('regex', self.clf.clf_type)
        self.assertEqual('\d', self.clf.expression)
        self.assertEqual(True, self.clf.reverse)

        # The classifier should match texts
        # which doesn't contain any digits at all
        expected_predictions = [True, False, False, True, False,
                                True, False, True]
        # Convert `numpy.ndarray` to `list`
        actual_predictions = list(
            self.clf.predict([
                ':)', '0!=1', '99.9%', 'Hello, world!', '2017-05-31',
                'Hasta la vista, baby!', 'Python 2.7', 'Spot'
            ])
        )
        self.assertEqual(expected_predictions, actual_predictions)

    # Legacy tests

    def setUp(self):
        super(RegexClassifierTest, self).setUp()
        self.expression = r'[0-9]+'
        self.X = ['nonmatching', 'matching10', '***000***matching']
        self.y_true = [False, True, True]
        self.text = '^a1_b2:c3 d45-ef67$'

    def test_predict_include(self):
        re_clf = RegexClassifier()
        re_clf.config(expression=self.expression, apply='include')
        re_clf.save()

        y_pred = re_clf.predict(self.X)
        self.assertEqual(self.y_true, list(y_pred))

    def test_predict_exclude(self):
        re_clf = RegexClassifier()
        re_clf.config(expression=self.expression, apply='exclude')
        re_clf.save()

        y_pred = re_clf.predict(self.X)
        self.assertEqual(self.y_true, list(~y_pred))

    def test_split_include(self):
        re_clf = RegexClassifier()
        re_clf.config(expression=self.expression, apply='include')
        re_clf.save()

        partition_actual = re_clf.split(self.text)
        partition_expected = [
            ('^a', False), ('1', True), ('_b', False), ('2', True),
            (':c', False), ('3', True), (' d', False), ('45', True),
            ('-ef', False), ('67', True), ('$', False)
        ]
        self.assertEqual(partition_expected, partition_actual)

    def test_split_exclude(self):
        re_clf = RegexClassifier()
        re_clf.config(expression=self.expression, apply='exclude')
        re_clf.save()

        partition_actual = re_clf.split(self.text)
        partition_expected = [
            ('^a', True), ('1', False), ('_b', True), ('2', False),
            (':c', True), ('3', False), (' d', True), ('45', False),
            ('-ef', True), ('67', False), ('$', True)
        ]
        self.assertEqual(partition_expected, partition_actual)


class BuiltInClassifierTest(GenericClassifierTest):

    @classmethod
    def get_clf_class(cls):
        return BuiltInClassifier

    def test_config(self):
        self.clf.config(
            model='Termination',
            apply='include',
            # Some unused params (should go into kwargs)
            x=1, y=2, z=3
        )

        self.assertEqual('builtin', self.clf.clf_type)
        self.assertEqual('Termination', self.clf.model)
        self.assertEqual(False, self.clf.reverse)


class TrainedClassifierTest(GenericClassifierTest):

    @classmethod
    def get_clf_class(cls):
        return TrainedClassifier

    def setUp(self):
        super(TrainedClassifierTest, self).setUp()

        self.dataset = Dataset.objects.create(
            name='trained_classifier_test',
            klasses=['Africa', 'Asia', 'Europe'],
            samples={
                'texts': ['Senegal', 'Ukraine', 'China',
                          'Egypt', 'Romania', 'India'],
                'labels': [0, 2, 1, 0, 2, 1]
            }
        )

    def test_config(self):
        self.clf.config(
            datasets=[{'id': self.dataset.id,
                       'mapping': {'neg': ['Africa', 'Asia'],
                                   'pos': ['Europe']}}],
            model='logreg',
            apply='include',
            # Some unused params (should go into kwargs)
            x=1, y=2, z=3
        )

        self.assertEqual('trained', self.clf.clf_type)
        self.assertEqual(True, self.clf.dirty)
        self.assertEqual('logreg', self.clf.model)
        self.assertEqual(False, self.clf.reverse)

        clf_datasets = self.clf.datasets.all()
        self.assertEqual(1, len(clf_datasets))
        self.assertEqual(self.dataset.pk, clf_datasets[0].pk)

        dataset_clfs = self.dataset.trained_classifiers.all()
        self.assertEqual(1, len(dataset_clfs))
        self.assertEqual(self.clf.pk, dataset_clfs[0].pk)

        dataset_mapping = DatasetMapping.objects.get(dataset=self.dataset,
                                                     clf_uuid=self.clf.uuid)
        self.assertEqual({'Africa': False, 'Asia': False, 'Europe': True},
                         dataset_mapping.mapping)
