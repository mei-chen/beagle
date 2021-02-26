from django.db import models


class DBLogEntry(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10)
    message = models.TextField()

    class Meta:
        abstract = True


class GeneralLog(DBLogEntry):
    pass


class SpecialLog(DBLogEntry):
    pass
