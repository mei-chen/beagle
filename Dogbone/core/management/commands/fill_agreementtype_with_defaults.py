from core.models import Document
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fill in NULLs with the default value in the agreement_type column'

    def handle(self, *args, **options):
        # Warning: will take a while, probably
        for d in Document.objects.filter(agreement_type=None):
            d.agreement_type = Document.GENERIC
            d.save()
