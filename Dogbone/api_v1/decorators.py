import functools

from django.conf import settings
from django import http

from beagle_simpleapi.base import EndpointView


def internal_or_403(view_func):
    """
    A view decorator which returns the provided view function,
    modified to return a 403 when the remote address is not in
    the list of internal IPs defined in settings.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_internal(request):
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
        return view_func(request, *args, **kwargs)
    return wrapper


def internal_or_exception(view_func):
    """
    A view decorator which returns the provided view function,
    modified to raise a EndpointView.UnauthorizedException when the remote address is not in
    the list of internal IPs defined in settings.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_internal(request):
            raise EndpointView.UnauthorizedException("Protected Endpoint")
        return view_func(request, *args, **kwargs)
    return wrapper


def is_internal(request):
    return request.META['REMOTE_ADDR'] in settings.INTERNAL_IPS
