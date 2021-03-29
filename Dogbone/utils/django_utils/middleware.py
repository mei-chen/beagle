#from http import get_client_ip
from django.utils.deprecation import MiddlewareMixin


class ClientAddressMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'client_ip'):
            return

        request.client_ip = get_client_ip(request)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip