from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Detail(models.Model):
    DEV = "dev"
    BETA = "beta"
    DEPLOY = "deploy"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    CHOICES = (
        (DEV, DEV),
        (BETA, BETA),
        (DEPLOY, DEPLOY),
        (STAGING, STAGING),
        (PRODUCTION, PRODUCTION)
    )

    name = models.CharField(
        max_length=300
    )
    env = models.CharField(
        max_length=300,
        choices=CHOICES
    )
    endpoint_protocol = models.CharField(
        max_length=300
    )
    email_domain = models.CharField(
        max_length=300
    )
    endpoint_domain = models.CharField(
        max_length=300
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __unicode__(self):
        return self.name
