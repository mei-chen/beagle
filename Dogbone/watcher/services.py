import json

from constance import config
from oauth2client.client import OAuth2WebServerFlow

from watcher.models import DropboxAccess, GoogleDriveAccess


def build_google_auth_flow(request):
    redirect_uri = request.build_absolute_uri(
        '/account/google_drive_auth_callback'
    )
    # For non-local servers always use SSL
    scheme, _, netloc_path = redirect_uri.partition('://')
    if not scheme.endswith('s'):  # http (OK only locally)
        if not (netloc_path.startswith('localhost') or
                netloc_path.startswith('127.0.0.1')):
            scheme += 's'  # https (switch to SSL)
            redirect_uri = scheme + '://' + netloc_path
    flow = OAuth2WebServerFlow(
        client_id=config.GOOGLE_DRIVE_CLIENT_ID,
        client_secret=config.GOOGLE_DRIVE_CLIENT_SECRET,
        scope='https://www.googleapis.com/auth/drive',
        redirect_uri=redirect_uri,
        approval_prompt='force'
    )
    return flow


def save_google_credentials(user, credentials):
    google_drive_access, _ = GoogleDriveAccess.objects.get_or_create(user=user)
    google_drive_access.credentials = json.loads(credentials.to_json())
    google_drive_access.save()


def check_cloud_access(user):
    try:
        dropbox_access = DropboxAccess.objects.get(user=user)
    except DropboxAccess.DoesNotExist:
        dropbox_access = None

    if dropbox_access:
        dropbox_access_token = dropbox_access.token
    else:
        dropbox_access_token = None

    try:
        google_drive_access = GoogleDriveAccess.objects.get(user=user)
    except GoogleDriveAccess.DoesNotExist:
        google_drive_access = None

    return bool(dropbox_access), dropbox_access_token, \
           bool(google_drive_access)


def revoke_cloud_access(user, model):
    try:
        access_object = model.objects.get(user=user)
        access_object.delete()
    except model.DoesNotExist:
        pass
