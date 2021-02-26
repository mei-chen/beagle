import csv
from optparse import make_option

from core.models import Sentence, ANNOTATION_TAG_TYPE
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Restore system annotations from CSV in the new db format'

    option_list = BaseCommand.option_list + (
        make_option('--csvfile', help='path from where to load the tags'),
    )

    def handle(self, *args, **options):
        if 'csvfile' not in options:
            raise CommandError('Please specify source csv file (absolute path pls)')

        with open(options['csvfile'], 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in csvreader:
                sentpk, lbl_str, sublbl_str, prt_str = row
                lbl = lbl_str.split('|')
                sublbl = sublbl_str.split('|')
                prt = prt_str.split('|')

                s = Sentence.objects.get(pk=sentpk)
                for l, sl, p in zip(lbl, sublbl, prt):
                    s.add_tag(user=s.doc.owner,
                              label=l,
                              sublabel=sl,
                              party=p,
                              approved=True,
                              annotation_type=ANNOTATION_TAG_TYPE)

                # Invalidate cache of the doc
                s.doc.invalidate_cache()
