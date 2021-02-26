import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from dogbone.tools import absolutify
from core.models import Document
from portal.tasks import log_intercom_custom_event


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = User.objects.filter(username='henry')
        for user in users:
            self.stdout.write('Updating username=%s, email=%s' % (user.username, user.email))
            # Log event times for each user upload
            documents = Document.objects.filter(owner=user)

            for document in documents:

                if not document.pending:
                    document_analysis = document.doclevel_analysis
                    cached_analysis = document.cached_analysis

                    # Created Time
                    created = document.created.strftime('%s')

                    # Average Party confidences
                    confidence_mean = (document_analysis['parties']['them']['confidence'] + document_analysis['parties']['you']['confidence']) / 2

                    # Generate link to report
                    report_url = absolutify(document.get_report_url())

                    # Get RLTE Counts
                    responsibilities, liabilities, terminations, external_references = 0, 0, 0, 0

                    # Skip agreements with no cached analysis
                    if cached_analysis is None:
                        responsibilities, liabilities, terminations, external_references = -1, -1, -1, -1
                    else:
                        try:
                            for s in cached_analysis['sentences']:
                                annotations = s['annotations']
                                # Count RLTs
                                if annotations is not None:
                                    for a in annotations:
                                        label = a['label']
                                        if label == 'RESPONSIBILITY':
                                            responsibilities += 1
                                        elif label == 'LIABILITY':
                                            liabilities += 1
                                        elif label == 'TERMINATION':
                                            terminations += 1
                                # Count Es
                                if s['external_refs'] is not None:
                                    external_references += len(s['external_refs'])
                        except TypeError as e:
                            logging.error('Error extracting metadata from document=%s. Exception: %s' % (str(document.uuid), str(e)))

                    # Log a document upload event in Intercom
                    upload_metadata = {"Title": document.title,
                                       "Source": '-'}

                    processed_metadata = {"Title": document.title,
                                          "Party Confidence Mean": confidence_mean,
                                          "Report Url": {"url": report_url, "value": "View Report"},
                                          "Responsibilities": responsibilities,
                                          "Liabilities": liabilities,
                                          "Terminations": terminations,
                                          "External References": external_references}

                    log_intercom_custom_event(email=user.email, event_name="Document Uploaded", metadata=upload_metadata, created_at=created)
                    log_intercom_custom_event(email=user.email, event_name="Document Processed", metadata=processed_metadata, created_at=created)
            

