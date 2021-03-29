from django.contrib.auth import authenticate, login
from django.utils.deprecation import MiddlewareMixin


class TokenAuthMiddleware(MiddlewareMixin):
    """ Authentication Middleware for authenticating a user via token """

    def process_request(self, request):
        """
        Authenticate a user via token
        :param request: The HTTP request to pre-process
        :return:
        """
        t = request.GET.get('token')
        if not t:
            return

        user = authenticate(token=t)
        if user:
            request.user = user
            # login(request, user)