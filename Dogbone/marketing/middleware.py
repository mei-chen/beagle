from .manager import ActionManager


class ActionManagerMiddleware(object):
    """ Attach an action_manager object to the request if the user object is available """

    def process_request(self, request):
        """
        Attach the `ActionManager` object
        :param request: The HTTP request to pre-process
        :return:
        """
        if (hasattr(request, 'user')
                and hasattr(request.user, 'is_authenticated')
                and request.user.is_authenticated
                and not request.user.is_anonymous()):

            request.action_manager = ActionManager(request.user)
        else:
            request.action_manager = ActionManager(None)