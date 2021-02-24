import json

# Django
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse

# REST framework
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet

# Misc
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError

# App
from watcher.api.serializers import CloudFolderSerializer
from watcher.models import DropboxAccess, GoogleDriveAccess, CloudFolder


class CloudAuthAPI(ViewSet):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _check_field(data, field):
        if not field in data:
            raise ValidationError("No '%s' specified." % field)

    @list_route(methods=['GET'])
    def dropbox_callback(self, request, *args, **kwargs):
        return render(request, 'watcher/dropbox.html')

    @list_route(methods=['POST'])
    def set_dropbox_access(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        self._check_field(data, 'token')
        token = data['token']
        DropboxAccess.objects.update_or_create(
            user=user, defaults={'token': token}
        )
        return Response()

    @list_route(methods=['DELETE'])
    def revoke_dropbox_access(self, request, *args, **kwargs):
        user = request.user
        DropboxAccess.objects.filter(user=user).delete()
        return Response()

    @staticmethod
    def _build_google_drive_oauth2_flow(request):
        redirect_uri = request.build_absolute_uri(
            reverse('cloud_auth-google-drive-callback')
        )
        flow = OAuth2WebServerFlow(
            client_id=settings.GOOGLE_DRIVE_CLIENT_ID,
            client_secret=settings.GOOGLE_DRIVE_CLIENT_SECRET,
            scope='https://www.googleapis.com/auth/drive',
            redirect_uri=redirect_uri,
            approval_prompt='force'
        )
        return flow

    def _set_google_drive_access(self, request, *args, **kwargs):
        user = request.user
        code = request.query_params.get('code')
        if code is None:
            return
        flow = self._build_google_drive_oauth2_flow(request)
        try:
            credentials = flow.step2_exchange(code)
        except FlowExchangeError:
            return
        # Convert OAuth2Credentials object to dict
        credentials = json.loads(credentials.to_json())
        GoogleDriveAccess.objects.update_or_create(
            user=user, defaults={'credentials': credentials}
        )

    @list_route(methods=['GET'])
    def google_drive_callback(self, request, *args, **kwargs):
        self._set_google_drive_access(request, *args, **kwargs)
        return HttpResponseRedirect('/#/online-folder')

    @list_route(methods=['DELETE'])
    def revoke_google_drive_access(self, request, *args, **kwargs):
        user = request.user
        GoogleDriveAccess.objects.filter(user=user).delete()
        return Response()

    @list_route(methods=['GET'])
    def check_access(self, request, *args, **kwargs):
        user = request.user

        payload = {
            cloud: {'access': False} for cloud in ['dropbox', 'google_drive']
        }

        dropbox_access = DropboxAccess.objects.filter(user=user).last()
        if dropbox_access:
            payload['dropbox']['access'] = True
            payload['dropbox']['token'] = dropbox_access.token

        google_drive_access = GoogleDriveAccess.objects.filter(user=user).last()
        if google_drive_access:
            payload['google_drive']['access'] = True
        else:
            flow = self._build_google_drive_oauth2_flow(request)
            auth_url = flow.step1_get_authorize_url()
            payload['google_drive']['auth_url'] = auth_url

        return Response(payload)


class CloudFolderAPI(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CloudFolderSerializer

    def get_queryset(self):
        return CloudFolder.objects.order_by('-created')

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)
