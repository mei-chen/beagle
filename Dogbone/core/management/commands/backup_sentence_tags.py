from optparse import make_option
from core.models import Sentence
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import csv
from unidecode import unidecode


class Command(BaseCommand):
    help = 'Save tags and suggested tags in a CSV for backup reasons'

    option_list = BaseCommand.option_list + (
        make_option('--csvfile', help='path to where to save the tags'),
    )

    def handle(self, *args, **options):
        if 'csvfile' not in options:
            raise CommandError('Please specify destination csv file')

        with open(options['csvfile'], 'w+') as fout:
            csvwriter = csv.writer(fout, delimiter=',', quotechar='"')
            q = Sentence.objects.filter(Q(tags__isnull=False) | Q(suggested_tags__isnull=False))

            for sentence in q:
                tags = None
                if sentence.tags and sentence.tags.get('tags') and isinstance(sentence.tags.get('tags'), list):
                    tags = '|'.join(sentence.tags.get('tags'))

                suggested_tags = None
                if sentence.suggested_tags and sentence.suggested_tags.get('tags') and isinstance(sentence.suggested_tags.get('tags'), list):
                    suggested_tags = '|'.join(sentence.suggested_tags.get('tags'))

                if tags or suggested_tags:
                    csvwriter.writerow((sentence.pk, unidecode(tags) if tags else tags,
                                        unidecode(suggested_tags) if suggested_tags else suggested_tags))



