from http import get_client_ip


class ClientAddressMiddleware(object):
    def process_request(self, request):
        if hasattr(request, 'client_ip'):
            return

        request.client_ip = get_client_ip(request)

