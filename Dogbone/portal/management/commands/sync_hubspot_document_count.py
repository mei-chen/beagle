from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portal.tasks import hubspot_get_vid, hubspot_update_contact_properties


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            # Update the documents uploaded attribute
            try:
                doc_count = user.details.get_document_upload_count()

                self.stdout.write("Get user=%s's hubspot VID" % (user.email))
                user_vid = hubspot_get_vid(email=user.email)

                self.stdout.write("Updating Hubspot user user=%s, VID=%s, with count %s" %
                                  (user.username, user_vid, doc_count))
                data = [{"property": "documents_uploaded",
                         "value": doc_count}]

                hubspot_update_contact_properties(email=user.email, data=data)

                self.stdout.write("Success! user=%s successfully updated in hubspot" % (user.email))
            except:
                self.stdout.write(user, "--An Error ocurred trying to update user's document count")
