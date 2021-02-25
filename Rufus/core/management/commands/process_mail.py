# Python
import logging
import sys
import syslog
import email
import validators

# Django
from django.core.management.base import BaseCommand, CommandError

# App
from core.process_mail import main_sample, main
from server.models import Detail

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def read_input(self):
        return sys.stdin.read()

    def handle(self, *args, **options):
        self.stdout.write('Processing the mail', ending='')
        logger.info("Processing the mail logger.info")
        print "Processing the mail print"

        content = sys.stdin.read()
        syslog.syslog('Process Email Started with Message: \n %s . . . . . . (First 2000 chars/%s chars) \n ===================== END OF MESSAGE ====================== \n\n' % (content[:2000], len(content)))
        # syslog.syslog('Process Email Started with Message: \n %s . . . . . . (Last 5000 chars/%s chars) \n ===================== END OF MESSAGE ====================== \n\n' % (content[len(content) - 5000:len(content)], len(content)))
        message = email.message_from_string(content)

        fullname, address = email.utils.parseaddr(message.get('To'))

        self.stdout.write(address, ending='')
        if not validators.email(address):
            raise CommandError('The email is not valid')

        domain = address.split("@")[-1]

        if not Detail.objects.filter(email_domain=domain).exists():
            raise CommandError('The domain for the email does not exist')

        main(message, domain, content)


        syslog.syslog('\n %s \n\n' % ('=' * 150))
