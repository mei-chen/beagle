import json
import logging

from beagle_simpleapi.endpoint import ComputeView, ListView, StatusView
from dogbone.actions import has_permission
from portal.files_processors import EncryptedZipArchiveProcessor
from watcher.models import Folder, DropboxAccess, GoogleDriveAccess
from watcher.services import (
    check_cloud_access, build_google_auth_flow, revoke_cloud_access
)


class UploadViewMixin(object):

    action_name = None  # no restrictions by default

    def allow(self, action):
        if self.action_name is None:  # always allowed
            return

        is_allowed, _ = has_permission(self.request, self.action_name)

        if not is_allowed:
            logging.warning('%s tried to %s without proper subscription',
                            self.user, action)
            raise self.UnauthorizedException(
                'You are not allowed to %s with your subscription' % action
            )


class RestrictedUploadViewMixin(UploadViewMixin):

    action_name = 'app_upload'


class ProcessEncryptedArchiveComputeView(ComputeView, RestrictedUploadViewMixin):

    url_pattern = r'/upload/set_password_for_zip$'
    endpoint_name = 'set_password_for_zip'

    def compute(self, request, *args, **kwargs):
        self.allow('process encrypted archive')

        processor = EncryptedZipArchiveProcessor(
            data=json.loads(request.body),
            user=request.user,
            time_zone=request.session.get('user_time_zone')
        )

        processor.main()
        message = processor.get_endpoint_message()

        # No need for serialization here, it will be made in parent's dispatch
        return message


class GetCloudAccessStatusView(StatusView, UploadViewMixin):

    url_pattern = r'/upload/get_cloud_access$'
    endpoint_name = 'get_cloud_access'

    def status(self, request, *args, **kwargs):
        self.allow('get cloud access')

        dropbox_access, dropbox_access_token, google_drive_access = \
            check_cloud_access(user=request.user)

        return {'dropbox': dropbox_access,
                'token': dropbox_access_token,
                'google-drive': google_drive_access}


class SetDropboxTokenComputeView(ComputeView, RestrictedUploadViewMixin):

    url_pattern = r'/upload/set_dropbox_token$'
    endpoint_name = 'set_dropbox_token'

    def compute(self, request, *args, **kwargs):
        self.allow('set dropbox token')

        token = json.loads(request.body)['token']
        user = request.user
        try:
            access = DropboxAccess.objects.get(user=user)
            access.token = token
            access.save()
        except DropboxAccess.DoesNotExist:
            DropboxAccess.objects.create(token=token, user=user)
        return {'message': 'Created', 'http_status': 201}


class SetGoogleDriveSecretStatusView(StatusView, RestrictedUploadViewMixin):

    url_pattern = r'/upload/set_google_drive_secret'
    endpoint_name = 'set_google_drive_secret'

    def status(self, request, *args, **kwargs):
        self.allow('set google drive secret')

        flow = build_google_auth_flow(request)
        auth_url = flow.step1_get_authorize_url()
        return {'accessUrl': auth_url}


class AddCloudFolderComputeView(ComputeView, RestrictedUploadViewMixin):

    url_pattern = r'/upload/add_cloud_folder$'
    endpoint_name = 'add_cloud_folder'

    def compute(self, request, *args, **kwargs):
        self.allow('add cloud folder')

        data = json.loads(request.body)

        user = request.user
        folder_id = data['folder_id']
        defaults = {'title': data['title'],
                    'cloud': data['cloud'],
                    'folder_path': data.get('folder_path')}

        Folder.objects.get_or_create(user=user,
                                     folder_id=folder_id,
                                     defaults=defaults)

        return {'message': 'OK'}


class GetCloudFoldersListView(ListView, UploadViewMixin):

    url_pattern = r'/upload/get_cloud_folders$'
    endpoint_name = 'get_cloud_folders'

    model = Folder

    def wrap_result(self, result):
        return result

    def get_queryset(self, request):
        return self.model.objects.filter(user=request.user).order_by('-created')

    def get_slice(self):
        return slice(None, None)  # no pagination

    def get(self, request, *args, **kwargs):
        self.allow('get cloud folders')

        return super(GetCloudFoldersListView, self).get(request,
                                                        *args, **kwargs)


class DeleteCloudFolderComputeView(ComputeView, UploadViewMixin):

    url_pattern = r'/upload/delete_cloud_folder$'
    endpoint_name = 'delete_cloud_folder'

    def compute(self, request, *args, **kwargs):
        self.allow('delete cloud folder')

        folder_id = request.POST.get('id')
        try:
            Folder.objects.get(id=folder_id).delete()
            return {'message': 'OK'}
        except Folder.DoesNotExist:
            raise self.NotFoundException('Folder does not exist')


class RevokeGoogleDriveAccessView(StatusView, UploadViewMixin):

    url_pattern = r'/upload/revoke_google_drive_access$'
    endpoint_name = 'revoke_google_drive_access'

    model = GoogleDriveAccess

    def status(self, request, *args, **kwargs):
        self.allow('revoke google drive access')

        revoke_cloud_access(request.user, self.model)
        return {}


class RevokeDropboxAccessView(StatusView, UploadViewMixin):

    url_pattern = r'/upload/revoke_dropbox_access$'
    endpoint_name = 'revoke_dropbox_access'

    model = DropboxAccess

    def status(self, request, *args, **kwargs):
        self.allow('revoke dropbox access')

        revoke_cloud_access(request.user, self.model)
        return {}
