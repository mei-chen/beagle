import csv
from optparse import make_option

from core.models import Sentence, SUGGESTED_TAG_TYPE, MANUAL_TAG_TYPE
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Restore tags and suggested tags from CSV in the new db format'

    option_list = BaseCommand.option_list + (
        make_option('--csvfile', help='path from where to load the tags'),
    )

    def handle(self, *args, **options):
        if 'csvfile' not in options:
            raise CommandError('Please specify source csv file (absolute path pls)')

        with open(options['csvfile'], 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in csvreader:
                sentpk, tags_str, suggtags_str = row
                tags = tags_str.split('|')
                suggtags = suggtags_str.split('|')

                s = Sentence.objects.get(pk=sentpk)
                for t in tags:
                    s.add_tag(user=s.doc.owner,
                              label=t,
                              approved=True,
                              annotation_type=MANUAL_TAG_TYPE)
                for st in suggtags:
                    s.add_tag(user=s.doc.owner,
                              label=st,
                              approved=False,
                              annotation_type=SUGGESTED_TAG_TYPE)

                # Invalidate cache of the doc
                s.doc.invalidate_cache()
