from django.db import models


class PendingManager(models.Manager):
    def get_query_set(self):
        return super(PendingManager, self).get_query_set().filter(
            pending=True)


class ReadyManager(models.Manager):
    def get_query_set(self):
        return super(ReadyManager, self).get_query_set().filter(
            pending=False)


class TrashManager(models.Manager):
    """
    Get all objects that are deleted
    """
    def get_query_set(self):
        return super(TrashManager, self).get_query_set().filter(trash=True)


class NotTrashManager(models.Manager):
    """
    Get all objects that aren't deleted
    """
    def get_query_set(self):
        return super(NotTrashManager, self).get_query_set().filter(trash=False)


class PendingModel(models.Model):
    """
    Abstract Django model for modeling objects that can be in a pending state
    (Example: A document that is being processed)
    """
    pending = models.BooleanField(null=False, default=False)

    # If a fatal error is encountered it will get stuck in pending mode
    failed = models.BooleanField(null=False, default=False)
    error_message = models.TextField('Error message', blank=True, null=True, default=None)

    # Model managers
    objects = models.Manager()
    ready_objects = ReadyManager()
    pending_objects = PendingManager()

    @property
    def is_pending(self):
        return self.pending

    @property
    def is_ready(self):
        return not self.is_pending

    class Meta:
        abstract = True


class TrashableModel(models.Model):
    """
    Abstract Django model for modeling objects that can be marked as deleted (not actually deleted from the db)
    """
    trash = models.BooleanField('Deleted', default=False)

    # Model managers
    objects = NotTrashManager()
    recycle_bin = TrashManager()
    everything = models.Manager()

    @property
    def is_trash(self):
        return self.trash

    class Meta:
        abstract = True
