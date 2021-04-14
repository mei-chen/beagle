import json
import logging

from django.views.generic import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import url
from django.conf import settings


class CsrfExemptView(View):
    """
    Make sure endpoints don't use CSRF protection
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CsrfExemptView, self).dispatch(request, *args, **kwargs)


class EndpointView(CsrfExemptView):

    url_pattern = None

    # The name of the view
    endpoint_name = None

    def __init__(self, **kwargs):
        super(EndpointView, self).__init__(**kwargs)

        self.user = None
        self.request = None
        self.args = None
        self.kwargs = None

    @classmethod
    def to_url(cls):
        return url(cls.url_pattern, csrf_exempt(cls.as_view()), name=cls.endpoint_name)

    class UnknownSerializedFormatException(Exception):
        """
        Raised when the API is asked to serialize to an unknown format
        """
        status_code = 400
        error_type = 'error'

    class UnauthenticatedException(Exception):
        """
        Raised when we don't have an authenticated user
        """
        status_code = 403
        error_type = 'error'

    class UnauthorizedException(Exception):
        """
        Raised when the user does not have access to the resource
        """
        status_code = 403
        error_type = 'error'

    class NotFoundException(Exception):
        """
        Raised when an object was not found
        """
        status_code = 404
        error_type = 'error'

    class BadRequestException(Exception):
        """
        Raised when something wrong is requested
        """
        status_code = 400
        error_type = 'error'

    class ServiceUnavailableException(Exception):
        """
        Raised when our API wasn't able to receive some requested data
        from another remote server via its API
        """
        status_code = 503
        error_type= 'error'

    @classmethod
    def build_error_response(cls, message, code, status, error_type='error'):
        """
        :param message: Human readable error explanation
        :param code: custom int error code, application specific
        :param status: int HTTP status
        :param error_type: type of error. Ex: error/warning/critical
        :return: dict
        """
        return {
            'message': message,
            'code': code,
            'type': error_type,
            'http_status': status
        }

    @classmethod
    def build_error_response_from_exception(cls, exception):
        """
        Build a error response dict from exception object
        :param exception:
        :return: dict
        """
        status_code = 400
        try:
            status_code = getattr(exception, 'status_code')
        except AttributeError:
            pass

        error_type = 'error'
        try:
            error_type = getattr(exception, 'error_type')
        except AttributeError:
            pass

        return cls.build_error_response(str(exception), None, status_code, error_type)

    @classmethod
    def not_found(cls, message, error_code):
        return cls.build_error_response(message, error_code, 404, 'error')


    @classmethod
    def forbidden(cls, message, error_code):
        return cls.build_error_response(message, error_code, 403, 'error')

    @classmethod
    def serialize(cls, data, format='json'):
        """
        Create a JSON string given a dict/list
        """
        if format == 'json':
            return json.dumps(data, sort_keys=True, indent=4)

        raise cls.UnknownSerializedFormatException("%s is not a recognized serialization method" % format)

    def wrap_result(self, result):
        """
        Override this is you need the results to be wrapped inside something
        """
        return result

    def authenticate_user(self):
        """
        Checks if the user is authenticated.
        If you want to handle only authenticated users,
        raise a `UnauthenticatedException` here

        - Override this in case you need a special kind of authentication
        or no authentication at all

        :returns The authenticated user
        """
        if not self.request.user.is_authenticated:
            raise self.UnauthenticatedException("Please authenticate")

        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        """
        - Check that the user is authenticated
        - Set the appropriate HTTP status
        - In case an exception occurs, handle the response accordingly
        """
        try:
            # Retain the request, args and kwargs for later use
            self.request = request
            self.args = args
            self.kwargs = kwargs

            self.user = self.authenticate_user()
            result = super(CsrfExemptView, self).dispatch(request, *args, **kwargs)

            http_status = 200
            if 'http_status' in result:
                http_status = result['http_status']

            wrapped_result = self.wrap_result(result)
            return HttpResponse(self.serialize(wrapped_result, request.GET.get('format', 'json')),
                                status=http_status, content_type='application/json')
        except Exception as e:
            message = 'Exception encountered in Beagle SimpleAPI: %s' % str(e)
            if settings.DEBUG:
                # Also prints the call stack traceback
                logging.exception(message)
            else:
                logging.error(message)
            result = self.build_error_response_from_exception(e)
            return HttpResponse(self.serialize(result, request.GET.get('format', 'json')),
                                status=result['http_status'], content_type='application/json')


class ModelView(EndpointView):
    """
    Useful for exposing a single object
    Example url_pattern: '/user/(?P<user_id>[0-9]+)'
    """

    # The model attached to the DetailView endpoint
    model = None

    class ModelAttachmentException(Exception):
        """
        Raised when the Endpoint is not properly defined
        """
        status_code = 403
        error_type = 'critical'

    class ModelNotSerializableException(Exception):
        """
        Raised when the model has no to_dict() method
        or other serialization issues
        """
        status_code = 400
        error_type = 'critical'

    @classmethod
    def to_dict(cls, model):
        """
        Get the serialized model
        Override this in case the model does not have a .to_dict method,
        or you want a specific result
        """
        try:
            return model.to_dict()
        except AttributeError:
            raise cls.ModelNotSerializableException("%s is not serializable" % cls.__name__)

    @staticmethod
    def get_url(model):
        """
        Get the URL for the object.
        Override this in case the object doesn't have a `get_url` method,
        or a specific behavior is needed
        """
        try:
            return model.get_url()
        except AttributeError:
            return None

    def has_access(self, instance):
        """
        Check that the current user is authorized to view the instance
        """
        return True

