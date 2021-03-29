from optparse import make_option
from core.models import Sentence
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import csv
from unidecode import unidecode


class Command(BaseCommand):
    help = 'Sentence.formatting structure changed from {"xml": [nodes]} to [nodes]'

    def handle(self, *args, **options):
        q = Sentence.objects.filter(Q(formatting__isnull=False))

        for sentence in q:
            if 'xml' in sentence.formatting:
                sentence.formatting = sentence.formatting['xml']
                sentence.save()
                print('.')
