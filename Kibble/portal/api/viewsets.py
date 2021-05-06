import json
import os
import shutil
import tempfile
import urllib
import zipfile
from io import BytesIO

from constance import config as constance_settings
from django.conf import settings as django_settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.core import exceptions as django_exceptions
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import validate_email
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import reverse
from itsdangerous import URLSafeSerializer
from rest_framework import exceptions as drf_exceptions
from rest_framework import status as drf_status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from analysis.models import Report
from core.models import AccessToken, generate_random_token
from core.utils import (
    user_to_dict,
    send_project_invite, revoke_project_invite,
    send_batch_invite, revoke_batch_invite,
)
from document.models import Document
from document.tasks import auto_process_file
from portal.api.filters import BatchFilter, FileFilter
from portal.api.serializers import (
    UserSerializer, BatchSerializer, FileSerializer, ProjectSerializer
)
from portal.constants import ProjectStatus
from portal.models import Batch, File, Project, Sentence
from portal.tasks import compress_project, gather_personal_data_from_batch
from utils.conversion import docx_to_pdf
from utils.personal_data import obfuscate_document


class UserAPI(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return [self.request.user]

    @action(detail=False,methods=['GET'])
    def generate_token(self, request, *args, **kwargs):
        user = self.request.user
        for token in Token.objects.filter(user=user):
            token.delete()

        token_key = Token.objects.create(user=user).key
        user.profile.auth_token = token_key
        user.profile.save()

        return Response(token_key)


def get_projects_queryset(user, projects=None):
    # Each user has full access to his/her own projects
    # and limited access to projects he/she is collaborating on;
    # projects without owner are treated as global
    # (i.e. shared among all users)

    if projects is None:
        projects = Project.objects.all()

    return projects.filter(
        Q(owner=None) | Q(owner=user) |
        Q(collaboration_invites__invitee=user)
    ).distinct()


def get_batches_queryset(user, batches=None):
    # Each user has full access to his/her own batches
    # and limited access to batches he/she is collaborating on;
    # batches without owner are treated as global
    # (i.e. shared among all users)

    # Take into account that access to some project
    # also implies access to all batches contained in that project

    if batches is None:
        batches = Batch.objects.all()

    projects = get_projects_queryset(user)

    return batches.filter(
        Q(owner=None) | Q(owner=user) |
        Q(collaboration_invites__invitee=user) |
        Q(project__in=projects)
    ).distinct()


def get_files_queryset(user, files=None):
    # Access to some batch also implies access to all files from that batch;
    # files which are not attached to any batch yet are accessible by everyone

    if files is None:
        files = File.objects.all()

    batches = get_batches_queryset(user)

    return files.filter(
        Q(batch=None) | Q(batch__in=batches)
    ).distinct()


class BatchAPI(ModelViewSet):
    queryset = Batch.objects.order_by('id')
    serializer_class = BatchSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = BatchFilter

    def get_queryset(self):
        user = self.request.user
        return get_batches_queryset(user, self.queryset)

    def update(self, request, *args, **kwargs):
        batch = self.get_object()
        add_project = request.data.pop('add_project', [])
        remove_project = request.data.pop('remove_project', [])
        batch.project.add(*add_project)
        batch.project.remove(*remove_project)
        batch.save()
        return super(BatchAPI, self).update(request, *args, **kwargs)

    def _check_owner(self, request, batch):
        if request.user != batch.owner:
            raise drf_exceptions.PermissionDenied('Access forbidden.')

    def destroy(self, request, *args, **kwargs):
        batch = self.get_object()
        self._check_owner(request, batch)
        batch.delete()
        return Response(status=drf_status.HTTP_204_NO_CONTENT)

    @action(detail=True,methods=['GET'])
    def list_collaborators(self, request, *args, **kwargs):
        batch = self.get_object()
        self._check_owner(request, batch)
        payload = {
            'collaborators': map(user_to_dict, batch.collaborators)
        }
        return Response(payload)

    @action(detail=True,methods=['POST'])
    def invite_collaborator(self, request, *args, **kwargs):
        batch = self.get_object()
        self._check_owner(request, batch)
        inviter = request.user
        email = request.data['email']
        try:
            validate_email(email)
        except django_exceptions.ValidationError:
            raise drf_exceptions.ValidationError('Invalid email address.')
        status, message = send_batch_invite(email, inviter, batch)
        if not status:
            raise drf_exceptions.ValidationError(message)
        return Response()

    @action(detail=True,methods=['POST'])
    def uninvite_collaborator(self, request, *args, **kwargs):
        batch = self.get_object()
        user = request.user
        username = request.data.get('username')
        if username and username != user.username:
            # Only the owner is allowed to revoke access from anyone,
            # though collaborators can only revoke access from themselves
            self._check_owner(request, batch)
        else:
            # The user revokes access from himself/herself
            username = user.username
        revoke_batch_invite(username, batch)
        return Response()

    @action(detail=True,methods=['GET'])
    def obfuscate(self, request, *args, **kwargs):
        qp = self.request.query_params
        obf_reports = json.loads(qp.get('reports', '{}'))

        sents = set()
        for id in obf_reports.keys():
            report = Report.objects.get(pk=id)
            for i, entry in enumerate(json.loads(report.json)):
                i = str(i)
                if i in obf_reports[id]:
                    sents.add((entry['sentence'], obf_reports[id][i]))
        sents = list(sents)

        return self._obfuscate(sents)

    @action(detail=True,methods=['GET'])
    def obfuscate_sents(self, request, *args, **kwargs):
        qp = self.request.query_params
        sents = json.loads(qp.get('sents', '[]'))
        sents = [(Sentence.objects.get(id=id).text, obf_type)
                 for id, obf_type in sents]

        return self._obfuscate(sents)

    def _obfuscate(self, sents):
        batch = self.get_object()
        files = File.objects.filter(batch=batch)
        docs = Document.objects.filter(source_file__in=files)
        obfuscated_docs = [(d.name, obfuscate_document(d, sents)) for d in docs]

        s = BytesIO()
        if batch.owner.profile.obfuscated_export_ext == 'PDF':
            tmp_dir = tempfile.mkdtemp()
            pdf_paths = []
            for i in range(len(obfuscated_docs)):
                name, doc = obfuscated_docs[i]
                path = os.path.join(tmp_dir, '%s.docx' % name)
                fl = open(path, 'wb')
                fl.write(doc.read())
                fl.close()
                docx_to_pdf(tmp_dir, path)
                pdf_paths.append(os.path.join(tmp_dir, '%s.pdf' % name))

            with zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED) as zip:
                for path in pdf_paths:
                    zip.write(path, os.path.basename(path))

            shutil.rmtree(tmp_dir)

        else:
            with zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED) as zip:
                for name, obfuscated in obfuscated_docs:
                    zip.writestr('%s-obfuscated.docx' % name, obfuscated.getvalue())

        resp = HttpResponse(
            s.getvalue(),
            content_type='application/x-zip-compressed'
        )
        resp['Content-Disposition'] = 'attachment; filename=%s.zip' % batch.name

        return resp

    @action(detail=True,methods=['GET'])
    def gather_personal_data(self, request, *args, **kwargs):
        batch = self.get_object()
        gather_personal_data_from_batch.delay(batch.pk,
                                              request.session.session_key)
        batch.personal_data_gathered = True
        batch.save()

        return Response()


class FileAPI(ModelViewSet):
    queryset = File.objects.order_by('id')
    serializer_class = FileSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = FileFilter

    def get_queryset(self):
        user = self.request.user
        return get_files_queryset(user, self.queryset)

    def create(self, request, *args, **kwargs):
        result = super(FileAPI, self).create(request, *args, **kwargs)

        # There is no id in case of zip file
        if result.data['id']:
            auto_process_file.delay(result.data['id'],
                                    request.user.id,
                                    request.session.session_key)
        else:
            with zipfile.ZipFile(request.data['content'], mode='r') as zf:
                for filename in zf.namelist():
                    if filename.startswith('__MACOSX'):
                        continue

                    file = zf.open(filename)
                    name = filename.split('/')[-1]
                    if name and not File.objects.filter(
                            file_name=name, batch=result.data['batch']
                    ).exists():
                        f = File(file_name=name,
                                 content=SimpleUploadedFile(
                                     name, file.read(), None))
                        f.batch_id = result.data['batch']
                        f.save()

                        auto_process_file.delay(
                            f.id,
                            request.user.id,
                            request.session.session_key)
        return result


class ProjectAPI(ModelViewSet):
    queryset = Project.objects.order_by('id')
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        status = self.request.query_params.get(
            'status', ProjectStatus.Active.value
        )
        return get_projects_queryset(user, self.queryset).filter(status=status)

    @action(detail=True,methods=['PATCH'])
    def compress(self, request, *args, **kwargs):
        project = self.get_object()
        compress_project.delay(project.id, request.session.session_key)
        return Response(status=drf_status.HTTP_201_CREATED)

    def _check_owner(self, request, project):
        if request.user != project.owner:
            raise drf_exceptions.PermissionDenied('Access forbidden.')

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        self._check_owner(request, project)
        project.delete()
        return Response(status=drf_status.HTTP_204_NO_CONTENT)

    @action(detail=True,methods=['GET'])
    def list_collaborators(self, request, *args, **kwargs):
        project = self.get_object()
        self._check_owner(request, project)
        payload = {
            'collaborators': map(user_to_dict, project.collaborators)
        }
        return Response(payload)

    @action(detail=True,methods=['POST'])
    def invite_collaborator(self, request, *args, **kwargs):
        project = self.get_object()
        self._check_owner(request, project)
        inviter = request.user
        email = request.data['email']
        try:
            validate_email(email)
        except django_exceptions.ValidationError:
            raise drf_exceptions.ValidationError('Invalid email address.')
        status, message = send_project_invite(email, inviter, project)
        if not status:
            raise drf_exceptions.ValidationError(message)
        return Response()

    @action(detail=True,methods=['POST'])
    def uninvite_collaborator(self, request, *args, **kwargs):
        project = self.get_object()
        user = request.user
        username = request.data.get('username')
        if username and username != user.username:
            # Only the owner is allowed to revoke access from anyone,
            # though collaborators can only revoke access from themselves
            self._check_owner(request, project)
        else:
            # The user revokes access from himself/herself
            username = user.username
        revoke_project_invite(username, project)
        return Response()


class IsNotAuthenticated(IsAuthenticated):

    def has_permission(self, request, view):
        return not super(IsNotAuthenticated, self).has_permission(request, view)


class DogboneAPI(ViewSet):
    permission_classes = [permissions.AllowAny]

    SERIALIZER_SECRET_KEY = '/*[dogbone]->(kibble)*/'

    @action(detail=False,methods=['GET'])
    def authorize(self, request, *args, **kwargs):
        connect_uri = request.build_absolute_uri(
            reverse('dogbone-connect')
        )
        login_uri = request.build_absolute_uri(
            reverse('dogbone-login')
        )
        dogbone_authorize_url = '{url}?{query}'.format(
            url=constance_settings.DOGBONE_AUTHORIZE_URL,
            query=urllib.urlencode(
                {'connect_uri': connect_uri, 'login_uri': login_uri}
            )
        )
        return HttpResponseRedirect(dogbone_authorize_url)

    @action(detail=False,methods=['POST'])
    def connect(self, request, *args, **kwargs):
        data = request.data

        defaults = data['user']
        username = defaults.pop('username')
        # The username field must always be treated as immutable
        user, _ = User.objects.update_or_create(username=username,
                                                defaults=defaults)

        access_token = data['access_token']
        while True:
            try:
                defaults = {'value': access_token}
                AccessToken.objects.update_or_create(owner=user,
                                                     defaults=defaults)
                break
            except:  # validation failed or collision occurred
                access_token = generate_random_token()

        payload = {'access_token': access_token}
        return Response(payload)

    @action(detail=False,methods=['GET'])
    def login(self, request, *args, **kwargs):
        try:
            serializer = URLSafeSerializer(self.SERIALIZER_SECRET_KEY)
            access_token = serializer.loads(
                request.query_params['access_token']
            )

            user = AccessToken.objects.get(value=access_token).owner

            # Login the user without a password
            backend = django_settings.AUTHENTICATION_BACKENDS[0]
            
            # Logout previous users if exists
            auth.logout(request)
            auth.login(request, user, backend=backend)

        except:  # authentication failed
            pass  # nothing to do

        return HttpResponseRedirect('/')
