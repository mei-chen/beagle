from django.core.management.base import BaseCommand
from core.models import Document, Batch


class Command(BaseCommand):
    help = 'Optimize old uploaded documents for batches support'

    def handle(self, *args, **options):
        documents = Document.objects.only('batch', 'original_name',
                                          'owner', 'created')
        old_documents_count = documents.filter(batch=None).count()
        self.stdout.write('Found: %d' % old_documents_count)
        self.stdout.flush()
        counter = 0
        for document in documents:
            batch = document.batch
            if not batch:
                batch = Batch(name=document.original_name,
                              owner=document.owner,
                              created=document.created)
                batch.save()
                document.batch = batch
                document.save()
                counter += 1
                self.stdout.write('Updated: %d/%d' % (counter, old_documents_count))
                self.stdout.flush()
            else:
                if batch.created > document.created:
                    batch.created = document.created
                    batch.save()
            # If the document is already in the batch, then nothing will happen
            batch.add_document(document)
        self.stdout.write('Completed!')
        self.stdout.flush()
