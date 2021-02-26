import tempfile
import webbrowser

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class OpenBrowserEmailBackend(BaseEmailBackend):
    """
    An email backend that opens HTML parts of emails sent
    in a local web browser, for testing during development.
    """

    def send_messages(self, email_messages):
        if not settings.DEBUG:
            return

        for message in email_messages:
            for body, content_type in getattr(message, "alternatives", []):
                if content_type == "text/html":
                    self.open_browser(body)

    def open_browser(self, body):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as fh:
            path = fh.name
            fh.write(body.encode('utf-8'))
            fh.flush()

        webbrowser.open_new_tab("file://" + path)
