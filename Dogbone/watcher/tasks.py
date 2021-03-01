import collections
import logging

from celery import shared_task
from dropbox.files import FileMetadata

from dogbone.app_settings.marketing_settings import WebApplicationSubscription
from marketing.models import PurchasedSubscription
from watcher.engine import HandleCloudFile
from watcher.interaction import (
    DropboxInteraction, GoogleDriveInteraction,
    QueueAdapter, SynchronizedAdapter,
)
from watcher.models import (
    CloudTypes,
    Folder,
    DropboxAccess, GoogleDriveAccess,
    Queue,
)


@shared_task
def add_to_queue_from_dropbox():
    queue_adapter = QueueAdapter()
    synchronized_adapter = SynchronizedAdapter()

    folders = Folder.objects.select_related(
        'user__details', 'user__dropboxaccess'
    ).filter(cloud=CloudTypes.DROPBOX)

    folders_by_user = collections.defaultdict(list)
    for folder in folders:
        folders_by_user[folder.user].append(folder)

    for user in folders_by_user:
        user_folders = folders_by_user[user]

        settings = user.details.settings
        if not (settings or {}).get('online_folder_watcher', False):
            logging.warning('Skipping user %s: online folder watcher disabled', user)
            continue

        if not user.is_superuser:
            subscriptions = PurchasedSubscription.get_current_subscriptions(user)
            for subscription in subscriptions:
                if issubclass(subscription.get_subscription(), WebApplicationSubscription):
                    break
            else:
                logging.warning('Skipping user %s: no proper active subscription found', user)
                continue

        try:
            user.dropboxaccess
        except DropboxAccess.DoesNotExist:
            logging.warning('Skipping user %s: no Dropbox access granted', user)
            continue

        for folder in user_folders:
            synchronized_ids = synchronized_adapter.get_ids(folder)
            queue_ids = queue_adapter.get_ids(folder)

            try:
                files = DropboxInteraction.get_files_list(
                    DropboxInteraction.auth(folder), folder
                )
            except Exception as exception:
                logging.error('\nFolder: %s\nException: %r', folder, exception)
                continue

            for file in files:
                if isinstance(file, FileMetadata):
                    file_id = file.id
                    if file_id not in synchronized_ids:
                        if file_id not in queue_ids:
                            Queue.objects.create(
                                cloud_id=file_id,
                                title=file.name,
                                folder=folder,
                                cloud_path=file.path_display,
                            )


@shared_task
def add_to_queue_from_google_drive():
    queue_adapter = QueueAdapter()
    synchronized_adapter = SynchronizedAdapter()

    folders = Folder.objects.select_related(
        'user__details', 'user__googledriveaccess'
    ).filter(cloud=CloudTypes.GOOGLE_DRIVE)

    folders_by_user = collections.defaultdict(list)
    for folder in folders:
        folders_by_user[folder.user].append(folder)

    for user in folders_by_user:
        user_folders = folders_by_user[user]

        settings = user.details.settings
        if not (settings or {}).get('online_folder_watcher', False):
            logging.warning('Skipping user %s: online folder watcher disabled', user)
            continue

        if not user.is_superuser:
            subscriptions = PurchasedSubscription.get_current_subscriptions(user)
            for subscription in subscriptions:
                if issubclass(subscription.get_subscription(), WebApplicationSubscription):
                    break
            else:
                logging.warning('Skipping user %s: no proper active subscription found', user)
                continue

        try:
            user.googledriveaccess
        except GoogleDriveAccess.DoesNotExist:
            logging.warning('Skipping user %s: no Google Drive access granted', user)
            continue

        for folder in user_folders:
            synchronized_ids = synchronized_adapter.get_ids(folder)
            queue_ids = queue_adapter.get_ids(folder)

            try:
                files = GoogleDriveInteraction.get_files_list(
                    GoogleDriveInteraction.auth(folder), folder
                )
            except Exception as exception:
                logging.error('\nFolder: %s\nException: %r', folder, exception)
                continue

            for file in files:
                if file['mimeType'] != 'application/vnd.google-apps.folder':
                    file_id = file['id']
                    if file_id not in synchronized_ids:
                        if file_id not in queue_ids:
                            Queue.objects.create(
                                cloud_id=file_id,
                                title=file['title'],
                                folder=folder,
                            )


@shared_task
def queue_worker():
    worker = HandleCloudFile()
    for queue_obj in QueueAdapter.get_queue_list():
        if queue_obj.cloud_path:
            worker.main(queue_obj, CloudTypes.DROPBOX)
        else:
            worker.main(queue_obj, CloudTypes.GOOGLE_DRIVE)
