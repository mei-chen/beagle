from __future__ import print_function

import sys
from django.core.management.base import BaseCommand
from optparse import make_option
from core.models import Document


class Command(BaseCommand):
    help = 'Regenerates inconsistent cache for specified documents (without reanalysis)'

    option_list = BaseCommand.option_list + (
        make_option('--uuid', help='comma-separated UUIDs of documents'),
    )

    def handle(self, *args, **options):
        uuids = options.get('uuid')
        if not uuids:
            documents = Document.objects.all()
        else:
            uuids = uuids.split(',')
            documents = Document.objects.filter(uuid__in=uuids)
        found = len(documents)
        regenerated = 0
        for document in documents:
            try:
                document.invalidate_cache()
                document.analysis_result
                regenerated += 1
                print('.', end='')
                sys.stdout.flush()
            except:
                pass
        print()
        print('Regenerated cache for %d documents (out of %d found).' % (regenerated, found))
