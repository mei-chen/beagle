from optparse import make_option
from core.models import Sentence
from django.core.management.base import BaseCommand, CommandError
import csv
from unidecode import unidecode


class Command(BaseCommand):
    help = 'Save system annotations in a CSV for backup reasons'

    option_list = BaseCommand.option_list + (
        make_option('--csvfile', help='path to where to save the tags'),
    )

    def handle(self, *args, **options):
        if 'csvfile' not in options:
            raise CommandError('Please specify destination csv file')

        with open(options['csvfile'], 'w+') as fout:
            csvwriter = csv.writer(fout, delimiter=',', quotechar='"')
            q = Sentence.objects.filter(labels__isnull=False)

            for sentence in q:
                labels = None
                sublabels = None
                parties = None
                if sentence.labels and isinstance(sentence.labels, list):
                    labels = '|'.join([l['label'] for l in sentence.labels])
                    sublabels = '|'.join([l['sublabel'] for l in sentence.labels])
                    parties = '|'.join([l['party'] for l in sentence.labels])

                if labels:
                    csvwriter.writerow((sentence.pk, unidecode(labels), sublabels, parties))
