import os
import tempfile

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from mock import patch, ANY
from model_mommy import mommy, recipe
from rest_framework.test import APITestCase

from core.models import ProjectCollaborationInvite, BatchCollaborationInvite
from core.utils import user_to_dict
from document.models import Document
from portal.constants import ProjectStatus
from portal.models import File, Batch, Project
from shared.mixins import PatcherMixin


filerecipe = recipe.Recipe(
    File,
    content=recipe.seq('mock.file')
)


class APIProjectTest(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('project-list')
        self.batch_list_url = reverse('batch-list')
        super(APIProjectTest, self).setUp()

    def project_uri(self, project):
        return reverse('project-detail', kwargs={
            'pk': project.pk,
        })

    def user_uri(self, user):
        return reverse('user-detail', kwargs={
            'pk': user.pk,
        })

    def batch_uri(self, batch):
        return reverse('batch-detail', kwargs={
            'pk': batch.pk,
        })

    def project_compress_uri(self, project):
        return self.project_uri(project) + 'compress/'

    def create_dataset(self):
        self.projects = baker.make(Project, 3, owner=self.user)
        self.p1_batches = baker.make(Batch, 3, project=[self.projects[0]])
        self.free_batch = baker.make(Batch)

        recipe = filerecipe.extend(batch=self.p1_batches[0])
        self.b1_files = (recipe.make(), recipe.make(), recipe.make())

    def test_project_api_requires_login(self):
        """
        Project API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_get_projects_list(self):
        """
        Project list should have batches and files subsets
        """
        self.create_dataset()
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        for i in range(3):
            self.assertEqual(data[i]['name'], self.projects[i].name)
            self.assertEqual(data[i]['id'], self.projects[i].id)
            self.assertEqual(
                data[i]['status'], self.projects[i].status)
            self.assertEqual(
                data[i]['status_verbose'],
                self.projects[i].get_status_display())
            self.assertEqual(
                data[i]['owner'],
                self.projects[i].owner.id)
            self.assertEqual(
                data[i]['owner_username'],
                self.projects[i].owner.username)
            self.assertEqual(
                data[i]['batch_count'],
                str(self.projects[i].batches.count())
            )
        self.assertIn('batches', data[0])
        self.assertEqual(len(data[0]['batches']), 3)
        for i in range(3):
            batch = data[0]['batches'][i]
            self.assertEqual(batch['id'], self.p1_batches[i].id)

    def test_create_project(self):
        """
        Project should be created on POST
        """
        self.client.force_login(self.user)
        data = {
            'name': 'FooName',
            'owner': self.user.id
        }
        response = self.client.post(self.list_url, data=data)
        self.assertEqual(response.status_code, 201)
        p = Project.objects.first()
        self.assertTrue(p)
        self.assertEqual(p.name, 'FooName')
        self.assertEqual(p.owner, self.user)

    def test_create_project_name_required(self):
        """
        Project should have non-blank name
        """
        self.client.force_login(self.user)
        data = {
            'name': None,
            'owner': self.user_uri(self.user)
        }
        response = self.client.post(self.list_url, data=data)
        self.assertEqual(response.status_code, 400)

        data['name'] = ''
        response = self.client.post(self.list_url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_edit_project(self):
        """
        Project should be edited on PUT
        """
        p = baker.make(Project)
        b = baker.make(Batch, project=[p])
        self.client.force_login(self.user)
        data = {
            'name': 'FooName',
            'owner': self.user.id
        }
        response = self.client.patch(self.project_uri(p), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.count(), 1)
        p = Project.objects.first()
        self.assertEqual(p.name, 'FooName')
        self.assertEqual(p.owner, self.user)
        self.assertEqual(list(p.batches.all()), [b])

    @patch('portal.tasks.compress_project.delay')
    def test_create_archive(self, delay):
        """
        Call will initiates compress task
        """
        self.create_dataset()
        self.client.force_login(self.user)
        response = self.client.patch(self.project_compress_uri(self.projects[0]))
        self.assertEqual(response.status_code, 201)
        delay.assert_called_once_with(self.projects[0].id, ANY)

    def test_archived_excluded(self):
        """
        By default archived project does not appear in response
        """
        self.create_dataset()
        self.client.force_login(self.user)
        archived = self.projects[0]
        archived.status = ProjectStatus.Archived.value
        archived.save()
        response = self.client.get(self.list_url).json()
        self.assertTrue(all(prj['status_verbose'] != 'Archived' for prj in response))

    def test_show_archived(self):
        """
        Can get list of archived projects by adding ?inactive=1
        """
        self.create_dataset()
        self.client.force_login(self.user)
        archived = self.projects[0]
        archived.status = ProjectStatus.Archived.value
        archived.save()
        response = self.client.get(self.list_url, {'status': ProjectStatus.Archived.value}).json()
        self.assertTrue(all(prj['status_verbose'] == 'Archived' for prj in response))

    @staticmethod
    def get_enpoint_url(name, project):
        return reverse('project-%s' % name.replace('_', '-'),
                       kwargs={'pk': project.pk})

    def test_list_collaborators(self):
        users = baker.make(User, 2)
        project = baker.make(Project, owner=self.user)

        list_collaborators_url = \
            self.get_enpoint_url('list_collaborators', project)

        self.client.force_login(self.user)

        ProjectCollaborationInvite.objects.create(
            invitee=users[0], inviter=self.user, project=project
        )

        response = self.client.get(list_collaborators_url)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        expected_data = {
            'collaborators': [user_to_dict(users[0])]
        }
        self.assertEqual(expected_data, actual_data)

        ProjectCollaborationInvite.objects.create(
            invitee=users[1], inviter=self.user, project=project
        )

        response = self.client.get(list_collaborators_url)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        expected_data = {
            'collaborators': [user_to_dict(users[1]), user_to_dict(users[0])]
        }
        self.assertEqual(expected_data, actual_data)

    def test_invite_collaborator(self):
        user = baker.make(User, email='user@test.com')
        project = baker.make(Project, owner=self.user)

        invite_collaborator_url = \
            self.get_enpoint_url('invite_collaborator', project)

        self.client.force_login(self.user)

        response = self.client.post(invite_collaborator_url,
                                    {'email': 'qwerty'}, format='json')
        self.assertEqual(400, response.status_code)  # FAILED (invalid email)

        response = self.client.post(invite_collaborator_url,
                                    {'email': self.user.email}, format='json')
        self.assertEqual(400, response.status_code)  # FAILED (self-inviting)

        response = self.client.post(invite_collaborator_url,
                                    {'email': user.email}, format='json')
        self.assertEqual(200, response.status_code)  # OK

        ProjectCollaborationInvite.objects.get(
            invitee=user, inviter=self.user, project=project
        )

        response = self.client.post(invite_collaborator_url,
                                    {'email': user.email}, format='json')
        self.assertEqual(400, response.status_code)  # FAILED (duplicate invite)

    def test_uninvite_collaborator(self):
        user = baker.make(User)
        project = baker.make(Project, owner=self.user)

        uninvite_collaborator_url = \
            self.get_enpoint_url('uninvite_collaborator', project)

        self.client.force_login(self.user)

        ProjectCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, project=project
        )

        # The owner revokes the collaborator's invitation
        response = self.client.post(uninvite_collaborator_url,
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            ProjectCollaborationInvite.objects.filter(
                invitee=user, project=project
            ).exists()
        )

        self.client.force_authenticate(user=user)

        ProjectCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, project=project
        )

        # The collaborator revokes his/her invitation
        response = self.client.post(uninvite_collaborator_url)
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            ProjectCollaborationInvite.objects.filter(
                invitee=user, project=project
            ).exists()
        )

    def test_user_collaboration_management_access(self):
        user = baker.make(User)
        project = baker.make(Project, owner=self.user)

        # The project isn't accessible for unauthenticated users
        # and isn't visible for non-collaborators

        detail_url = self.get_enpoint_url('detail', project)

        self.client.force_authenticate(user=None)

        response = self.client.get(detail_url)
        self.assertEqual(401, response.status_code)

        self.client.force_authenticate(user=user)

        response = self.client.get(detail_url)
        self.assertEqual(404, response.status_code)

        # Though even for collaborators some endpoints aren't permitted

        ProjectCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, project=project
        )

        list_collaborators_url = \
            self.get_enpoint_url('list_collaborators', project)
        response = self.client.get(list_collaborators_url)
        self.assertEqual(403, response.status_code)

        invite_collaborator_url = \
            self.get_enpoint_url('invite_collaborator', project)
        response = self.client.post(invite_collaborator_url)
        self.assertEqual(403, response.status_code)

        # The collaborator can only revoke his/her invitation

        uninvite_collaborator_url = \
            self.get_enpoint_url('uninvite_collaborator', project)

        response = self.client.post(uninvite_collaborator_url,
                                    {'username': 'qwerty'}, format='json')
        self.assertEqual(403, response.status_code)  # FAILED (forbidden)

        response = self.client.post(uninvite_collaborator_url,
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)  # OK

        self.assertFalse(
            ProjectCollaborationInvite.objects.filter(
                invitee=user, project=project
            ).exists()
        )

    def test_accessible_projects(self):
        user = baker.make(User)
        projects = baker.make(Project, 4, owner=None)

        projects[1].owner = self.user
        projects[1].save()

        projects[2].owner = user
        projects[2].save()

        ProjectCollaborationInvite.objects.create(
            invitee=self.user, inviter=user, project=projects[2]
        )

        projects[3].owner = user
        projects[3].save()

        self.client.force_login(self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertEqual(3, len(data))

        expected_projects_ids = [project.id for project in projects[:3]]
        actual_projects_ids = [entry['id'] for entry in data]
        self.assertEqual(expected_projects_ids, actual_projects_ids)


class APIBatchTest(APITestCase, PatcherMixin):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('batch-list')
        super(APIBatchTest, self).setUp()

    def project_uri(self, project):
        return reverse('project-detail', kwargs={
            'pk': project.pk,
        })

    def batch_uri(self, batch):
        return reverse('batch-detail', kwargs={
            'pk': batch.pk,
        })

    def create_dataset(self):
        self.projects = baker.make(Project, 4)
        self.p1_batches = baker.make(Batch, 3, project=[self.projects[0]])
        self.p2_batches = baker.make(Batch, 3, project=[self.projects[1]])
        self.free_batches = baker.make(Batch, 2)

        recipe = filerecipe.extend(batch=self.p1_batches[0])
        self.b1_files = (recipe.make(), recipe.make(), recipe.make())

        recipe = filerecipe.extend(batch=self.free_batches[0])
        self.bf_files = (recipe.make(), recipe.make(), recipe.make())

    def test_batch_api_requires_login(self):
        """
        Batch API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_get_batches_list_for_project(self):
        """
        API should return batches for specified project
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        response = self.client.get(self.list_url, data={
            'project': self.projects[0].id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        for i in range(3):
            batch = data[i]
            self.assertEqual(batch['name'], self.p1_batches[i].name)
            self.assertEqual(
                batch['filecount'], self.p1_batches[i].files.count())
        self.assertIn('files', data[0])
        self.assertEqual(len(data[0]['files']), 3)
        for i in range(3):
            fileobj = data[0]['files'][i]
            self.assertEqual(
                fileobj['filename'],
                self.b1_files[i].file_name)

    def test_get_batches_list_no_project(self):
        """
        API should return batches that haven't assigned to specified project
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        expected = Batch.objects.exclude(project=self.projects[0])
        response = self.client.get(self.list_url, data={
            'unassigned': self.projects[0].id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), expected.count())
        for i in range(2):
            batch = data[i]
            self.assertEqual(batch['name'], expected[i].name)
            self.assertIn('files', batch)
            files = expected[i].files.all()
            self.assertEqual(len(batch['files']), files.count())
            for j in range(files.count()):
                fileobj = batch['files'][j]
                self.assertEqual(
                    fileobj['filename'],
                    files[j].content.name.split('/')[-1])

    def test_assign_batch_to_project(self):
        """
        API should allow assigning batch to project
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        b = self.p2_batches[0]
        data = {
            'project': [self.projects[0].id]
        }
        response = self.client.patch(
            self.batch_uri(b), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.project.first(), self.projects[0])
        self.assertEqual(self.projects[0].batches.count(), 4)
        self.assertEqual(self.projects[1].batches.count(), 2)

    def test_add_batch_to_project(self):
        """
        API should allow adding batch to project
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        b = self.free_batches[0]
        data = {
            'project': [self.projects[0].id]
        }
        response = self.client.patch(
            self.batch_uri(b), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.project.first(), self.projects[0])
        self.assertEqual(self.projects[0].batches.count(), 4)

    def test_add_batch_to_other_project(self):
        """
        API should allow adding batch to other project
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        b = self.p2_batches[0]
        data = {
            'add_project': [self.projects[0].id, self.projects[2].id]
        }
        response = self.client.patch(
            self.batch_uri(b), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(set(b.project.all()), set(self.projects[:3]))
        self.assertEqual(self.projects[0].batches.count(), 4)
        self.assertEqual(self.projects[1].batches.count(), 3)
        self.assertEqual(self.projects[2].batches.count(), 1)

    def test_remove_batch_from_all_projects(self):
        """
        API should allow removing batch from all projects
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        b = self.p1_batches[0]
        b.project.add(self.projects[1])
        data = {
            'project': []
        }
        response = self.client.patch(
            self.batch_uri(b), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.project.count(), 0)
        self.assertEqual(self.projects[0].batches.count(), 2)
        self.assertEqual(self.projects[1].batches.count(), 3)

    def test_remove_batch_from_project(self):
        """
        API should allow removing batch from specified project(s)
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        b = self.p1_batches[0]
        b.project.add(self.projects[1])
        b.project.add(self.projects[2])
        data = {
            'remove_project': [self.projects[0].id, self.projects[2].id]
        }
        response = self.client.patch(
            self.batch_uri(b), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.project.count(), 1)
        self.assertEqual(self.projects[0].batches.count(), 2)
        self.assertEqual(self.projects[1].batches.count(), 4)

    def test_batch_has_owner(self):
        """
        Batch can has an owner
        """
        batch_w_owner = baker.make(Batch, owner=self.user)
        self.client.force_login(self.user)
        response = self.client.get(self.batch_uri(batch_w_owner))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['owner'], self.user.id)
        self.assertEqual(data['owner_username'], self.user.username)

    def test_rename_batch(self):
        """
        API should allow batch renaming/description editing
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        b = self.free_batches[0]
        data = {
            'name': 'Foo Batch',
            'description': 'A foo batch'
        }
        expected = model_to_dict(b)
        expected.update(data)
        response = self.client.patch(
            self.batch_uri(b), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.name, data['name'])
        self.assertEqual(b.description, data['description'])

    @patch('portal.models.Batch._sentences_count')
    def test_batch_list_contains_sentences_count(self, count_mock):
        """
        API should return sentences_count for batches
        """
        count_mock.return_value = 123
        self.create_dataset()
        self.client.force_login(self.user, )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 8)
        self.assertTrue(count_mock.called)
        self.assertIn('sentences_count', data[0])
        self.assertEqual(data[0]['sentences_count'], 123)

    @staticmethod
    def get_enpoint_url(name, batch):
        return reverse('batch-%s' % name.replace('_', '-'),
                       kwargs={'pk': batch.pk})

    def test_list_collaborators(self):
        users = baker.make(User, 2)
        batch = baker.make(Batch, owner=self.user)

        list_collaborators_url = \
            self.get_enpoint_url('list_collaborators', batch)

        self.client.force_login(self.user)

        BatchCollaborationInvite.objects.create(
            invitee=users[0], inviter=self.user, batch=batch
        )

        response = self.client.get(list_collaborators_url)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        expected_data = {
            'collaborators': [user_to_dict(users[0])]
        }
        self.assertEqual(expected_data, actual_data)

        BatchCollaborationInvite.objects.create(
            invitee=users[1], inviter=self.user, batch=batch
        )

        response = self.client.get(list_collaborators_url)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        expected_data = {
            'collaborators': [user_to_dict(users[1]), user_to_dict(users[0])]
        }
        self.assertEqual(expected_data, actual_data)

    def test_invite_collaborator(self):
        user = baker.make(User, email='user@test.com')
        batch = baker.make(Batch, owner=self.user)

        invite_collaborator_url = \
            self.get_enpoint_url('invite_collaborator', batch)

        self.client.force_login(self.user)

        response = self.client.post(invite_collaborator_url,
                                    {'email': 'qwerty'}, format='json')
        self.assertEqual(400, response.status_code)  # FAILED (invalid email)

        response = self.client.post(invite_collaborator_url,
                                    {'email': self.user.email}, format='json')
        self.assertEqual(400, response.status_code)  # FAILED (self-inviting)

        response = self.client.post(invite_collaborator_url,
                                    {'email': user.email}, format='json')
        self.assertEqual(200, response.status_code)  # OK

        BatchCollaborationInvite.objects.get(
            invitee=user, inviter=self.user, batch=batch
        )

        response = self.client.post(invite_collaborator_url,
                                    {'email': user.email}, format='json')
        self.assertEqual(400, response.status_code)  # FAILED (duplicate invite)

    def test_uninvite_collaborator(self):
        user = baker.make(User)
        batch = baker.make(Batch, owner=self.user)

        uninvite_collaborator_url = \
            self.get_enpoint_url('uninvite_collaborator', batch)

        self.client.force_login(self.user)

        BatchCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, batch=batch
        )

        # The owner revokes the collaborator's invitation
        response = self.client.post(uninvite_collaborator_url,
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            BatchCollaborationInvite.objects.filter(
                invitee=user, batch=batch
            ).exists()
        )

        self.client.force_authenticate(user=user)

        BatchCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, batch=batch
        )

        # The collaborator revokes his/her invitation
        response = self.client.post(uninvite_collaborator_url)
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            BatchCollaborationInvite.objects.filter(
                invitee=user, batch=batch
            ).exists()
        )

    def test_user_collaboration_management_access(self):
        user = baker.make(User)
        batch = baker.make(Batch, owner=self.user)

        # The batch isn't accessible for unauthenticated users
        # and isn't visible for non-collaborators

        detail_url = self.get_enpoint_url('detail', batch)

        self.client.force_authenticate(user=None)

        response = self.client.get(detail_url)
        self.assertEqual(401, response.status_code)

        self.client.force_authenticate(user=user)

        response = self.client.get(detail_url)
        self.assertEqual(404, response.status_code)

        # Though even for collaborators some endpoints aren't permitted

        BatchCollaborationInvite.objects.create(
            invitee=user, inviter=self.user, batch=batch
        )

        list_collaborators_url = \
            self.get_enpoint_url('list_collaborators', batch)
        response = self.client.get(list_collaborators_url)
        self.assertEqual(403, response.status_code)

        invite_collaborator_url = \
            self.get_enpoint_url('invite_collaborator', batch)
        response = self.client.post(invite_collaborator_url)
        self.assertEqual(403, response.status_code)

        # The collaborator can only revoke his/her invitation

        uninvite_collaborator_url = \
            self.get_enpoint_url('uninvite_collaborator', batch)

        response = self.client.post(uninvite_collaborator_url,
                                    {'username': 'qwerty'}, format='json')
        self.assertEqual(403, response.status_code)  # FAILED (forbidden)

        response = self.client.post(uninvite_collaborator_url,
                                    {'username': user.username}, format='json')
        self.assertEqual(200, response.status_code)  # OK

        self.assertFalse(
            BatchCollaborationInvite.objects.filter(
                invitee=user, batch=batch
            ).exists()
        )

    def test_accessible_batches(self):
        users = baker.make(User, 2)
        projects = baker.make(Project, 6, owner=None)
        batches = []

        batches.append(
            baker.make(Batch, owner=None, project=[])
        )
        batches.append(
            baker.make(Batch, owner=self.user, project=[])
        )

        baker.make(Batch, owner=users[0], project=[])
        baker.make(Batch, owner=users[1], project=[])

        batches.append(
            baker.make(Batch, owner=users[0], project=[projects[0]])
        )
        batches.append(
            baker.make(Batch, owner=users[1], project=[projects[0]])
        )

        projects[1].owner = self.user
        projects[1].save()

        batches.append(
            baker.make(Batch, owner=self.user, project=[projects[1]])
        )

        projects[2].owner = users[0]
        projects[2].save()

        ProjectCollaborationInvite.objects.create(
            invitee=self.user, inviter=users[0], project=projects[2]
        )

        batches.append(
            baker.make(Batch, owner=users[0], project=[projects[2]])
        )

        projects[3].owner = users[1]
        projects[3].save()

        ProjectCollaborationInvite.objects.create(
            invitee=self.user, inviter=users[1], project=projects[3]
        )

        batches.append(
            baker.make(Batch, owner=users[1], project=[projects[3]])
        )

        projects[4].owner = users[0]
        projects[4].save()

        batches.append(
            baker.make(Batch, owner=users[0], project=[projects[1], projects[4]])
        )

        baker.make(Batch, owner=users[0], project=[projects[4]])

        batches.append(
            baker.make(Batch, owner=users[0], project=[projects[4]])
        )

        BatchCollaborationInvite.objects.create(
            invitee=self.user, inviter=users[0], batch=batches[-1]
        )

        projects[5].owner = users[1]
        projects[5].save()

        baker.make(Batch, owner=users[1], project=[projects[5]])

        batches.append(
            baker.make(Batch, owner=users[1], project=[projects[1], projects[5]])
        )

        batches.append(
            baker.make(Batch, owner=users[1], project=[projects[5]])
        )

        BatchCollaborationInvite.objects.create(
            invitee=self.user, inviter=users[1], batch=batches[-1]
        )

        self.client.force_login(self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertEqual(len(batches), len(data))

        expected_batches_ids = [batch.id for batch in batches]
        actual_batches_ids = [entry['id'] for entry in data]
        self.assertEqual(expected_batches_ids, actual_batches_ids)


class LocalUploadTest(APITestCase):
    def setUp(self):
        super(LocalUploadTest, self).setUp()
        self.user = baker.make(User)
        self.batch = baker.make(Batch, name='Foo')
        recipe = filerecipe.extend(batch=self.batch)
        self.files = (recipe.make(), recipe.make())
        self.batch_api_url = reverse('batch-list')
        self.file_api_url = reverse('file-list')

    @classmethod
    def setUpClass(cls):
        super(LocalUploadTest, cls).setUpClass()
        cls.tmpfile = tempfile.mkstemp()[1]
        open(cls.tmpfile, 'w').write('CONTENT')

    def test_get_batches(self):
        """
        Check json's response structure
        """
        self.client.force_login(self.user)
        response = self.client.get(self.batch_api_url)
        response_data = response.json()
        self.assertIn(
            self.batch.files.first().content.url,
            response_data[0]['files'][0]['content']
        )

    @patch('document.tasks.auto_process_file.delay')
    def test_post_add_files(self, delay):
        """
        Add file to the batch
        """
        self.client.force_login(self.user)
        with open(self.tmpfile, 'r') as f:
            response = self.client.post(
                self.file_api_url,
                data={
                    'content': f,
                    'batch': self.batch.pk
                },
            )

        self.assertEqual(response.status_code, 201)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.files.count(), 3)
        file = self.batch.files.last()
        self.assertIn(
            os.path.basename(self.tmpfile),
            file.content.name
        )
        self.assertEqual(os.path.basename(self.tmpfile), file.file_name)
        delay.assert_called_once_with(ANY, self.user.pk, ANY)

    @patch('document.tasks.auto_process_file.delay')
    def test_post_add_duplicate_files(self, delay):
        """
        Do not add duplicate file to batch
        """
        self.client.force_login(self.user)
        with open(self.tmpfile, 'r') as f:
            self.client.post(
                self.file_api_url,
                data={
                    'content': f,
                    'batch': self.batch.pk
                },
            )

        with open(self.tmpfile, 'r') as f:
            response = self.client.post(
                self.file_api_url,
                data={
                    'content': f,
                    'batch': self.batch.pk
                },
            )

        self.assertEqual(response.status_code, 400)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.files.count(), 3)
        delay.assert_called_once_with(ANY, self.user.pk, ANY)

    def test_post_create_batch(self):
        """
        Create new batch without file
        """
        self.client.force_login(self.user)
        response = self.client.post(
            self.batch_api_url,
            data={'name': 'Lorem'},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        last_batch = Batch.objects.last()
        self.assertEqual(last_batch.name, 'Lorem')

    def test_returning_data_on_post_request(self):
        """
        Check if always_return_data is set
        """
        self.client.force_login(self.user)
        response = self.client.post(
            self.batch_api_url,
            data={'name': 'Combat'},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()['name'], 'Combat',
        )

    @patch('document.tasks.auto_process_file.delay')
    def test_post_process_txt_file(self, delay):
        """
        Add txt file to the batch
        """
        self.client.force_login(self.user)
        name = '-donnell-strategic-industrial-reit-inc-1503993-2012-11-14'
        file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data', name
        )
        with open(file, 'r') as f:
            response = self.client.post(
                self.file_api_url,
                data={
                    'content': f,
                    'batch': self.batch.pk
                },
            )

        self.assertEqual(response.status_code, 201)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.files.count(), 3)
        file = self.batch.files.last()
        self.assertEqual(file.type, File.FILE_TXT)
        self.assertEqual(name, file.file_name)
        self.assertIn(name, file.content.name)
        delay.assert_called_once_with(response.data['id'], self.user.id, ANY)


class APIFileTest(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('file-list')
        super(APIFileTest, self).setUp()

    def file_uri(self, fileinst):
        return reverse('file-detail', kwargs={
            'pk': fileinst.pk,
        })

    def batch_uri(self, batch):
        return reverse('batch-detail', kwargs={
            'pk': batch.pk,
        })

    def create_dataset(self):
        self.batches = baker.make(Batch, 2)
        recipe = filerecipe.extend(batch=self.batches[0])
        self.b1_files = [recipe.make(), recipe.make(), recipe.make()]
        recipe = filerecipe.extend(batch=self.batches[1])
        self.b2_files = [recipe.make(), recipe.make(), recipe.make()]
        self.converted_file = baker.make(File, batch=self.batches[0])
        self.document = baker.make(Document, source_file=self.converted_file)

    def test_batch_api_requires_login(self):
        """
        File API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_get_files_list_for_batch(self):
        """
        API should return files for specified batch
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        response = self.client.get(self.list_url, data={
            'batch': self.batches[0].id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.b1_files.append(self.converted_file)
        self.assertEqual(len(data), 4)
        for i in range(4):
            content = data[i]
            self.assertEqual(
                content['filename'],
                self.b1_files[i].file_name)

    def test_get_nonconverted_files_list_for_batch(self):
        """
        API should return non-converted files for specified batch
        """
        self.create_dataset()
        self.client.force_login(self.user, )
        response = self.client.get(self.list_url, data={
            'batch': self.batches[0].id,
            'nodocuments': True
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        for i in range(3):
            content = data[i]
            self.assertEqual(
                content['filename'],
                self.b1_files[i].content.name.split('/')[-1])

    def test_api_returns_free_files(self):
        """
        API should return unassigned files
        """
        self.client.force_login(self.user)
        self.create_dataset()

        response = self.client.get(self.list_url, data={
            'unassigned': True
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        all_free_files = File.objects.filter(batch__isnull=True)
        self.assertEqual(
            sorted(d['id'] for d in data),
            sorted(f.id for f in all_free_files)
        )

    def test_api_returns_files_for_batch(self):
        """
        API should return files for specified batch
        """
        self.client.force_login(self.user)
        self.create_dataset()

        response = self.client.get(self.list_url, data={
            'batch': self.batches[0].id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            sorted(d['id'] for d in data),
            sorted(f.id for f in self.b1_files + [self.converted_file])
        )

    def test_add_file_to_batch(self):
        """
        API should allow adding file to batch
        """
        self.client.force_login(self.user)
        batch = baker.make(Batch, project=[baker.make(Project)])
        free_file = baker.make(File, batch=None)
        data = {
            'batch': batch.pk
        }

        self.assertNotEqual(free_file.batch, batch)
        response = self.client.patch(
            self.file_uri(free_file), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        free_file.refresh_from_db()
        self.assertEqual(free_file.batch, batch)

    def test_remove_files_from_batch(self):
        """
        API should allow removing files from batch
        """
        self.client.force_login(self.user)
        batch = baker.make(Batch, project=[baker.make(Project)])
        binded_files = baker.make(File, batch=batch)
        data = {
            'batch': None
        }

        self.assertEqual(binded_files.batch, batch)
        response = self.client.patch(
            self.file_uri(binded_files), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        binded_files.refresh_from_db()
        self.assertNotEqual(binded_files.batch, batch)

    def test_accessible_batches(self):
        user = baker.make(User)
        projects = [baker.make(Project, owner=owner)
                    for owner in [self.user, user]]
        batches = [baker.make(Batch, owner=None, project=[projects[index]])
                   for index in [0, 0, 1, 1, 1, 1]]
        files = []

        files.append(baker.make(File, batch=None))

        files.append(baker.make(File, batch=batches[0]))

        batches[1].owner = self.user
        batches[1].save()

        files.append(baker.make(File, batch=batches[1]))

        files.append(baker.make(File, batch=batches[2]))

        batches[3].owner = user
        batches[3].save()

        baker.make(File, batch=batches[3])

        batches[4].owner = user
        batches[4].save()

        BatchCollaborationInvite.objects.create(
            invitee=self.user, inviter=user, batch=batches[4]
        )

        files.append(baker.make(File, batch=batches[4]))

        batches[5].owner = self.user
        batches[5].save()

        files.append(baker.make(File, batch=batches[5]))

        self.client.force_login(self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertEqual(len(files), len(data))

        expected_files_ids = [batch.id for batch in files]
        actual_files_ids = [entry['id'] for entry in data]
        self.assertEqual(expected_files_ids, actual_files_ids)
