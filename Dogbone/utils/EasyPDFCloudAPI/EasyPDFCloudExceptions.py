import http.client

class EasyPDFCloudArgumentException(Exception):
    """ Used to handle all invalid arguments passed to functions in the API. """

    def __init__(self, message):
        super(Exception, self).__init__()
        self.message = message

    def __str__(self):
        return "Error: %s." % self.message

    def __repr__(self):
        return "EasyPDFCloudArgumentException(%r)" % self.message


class EasyPDFCloudHTTPException(http.client.HTTPException):
    """ Used to handle all HTTP related exceptions in the API. """

    def __init__(self, status_code, reason, error=None, description_or_source=None):
        super(http.client.HTTPException, self).__init__()
        self.status_code = status_code
        self.reason = reason
        self.error = error or "N/A"
        self.description_or_source = description_or_source or "N/A"

    def __str__(self):
        return "%d: %s. Error: %s. Description/Source: %s." % (self.status_code, self.reason, self.error, self.description_or_source)

    def __repr__(self):
        return "EasyPDFCloudHTTPException(%r, %r, %r, %r)" % (self.status_code, self.reason, self.error, self.description_or_source)
