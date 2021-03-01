import logging

from .tools import get_all_subclasses
from .exceptions import ActionDoesNotExist


def autodiscover():
    """
    Auto-discover INSTALLED_APPS actions.py modules and fail silently when
    not present.
    """

    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)

        if mod.__name__.startswith('django.'):
            continue

        # Attempt to import the app's report module.
        try:
            import_module('%s.actions' % app)
            logging.info('Imported %s.actions.py file' % app)
        except ImportError:
            # Decide whether to bubble up this error. If the app just
            # doesn't have an reports module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'actions'):
                raise


class Action(object):
    """
    encapsulate an User's action name and parameters
    """
    name = 'ABSTRACT_ACTION'

    @staticmethod
    def get_actions():
        return get_all_subclasses(Action)

    @staticmethod
    def get_action_by_name(name):
        """
        Get the action by name. Get all the subclasses of Action and filter by name
        :param name: the name of the action
        :return: `marketing.action.Action` object or `None`
        """
        try:
            return [a for a in Action.get_actions() if a.name == name][0]
        except IndexError:
            raise ActionDoesNotExist('Action `%s` does not exist' % name)

    def __init__(self, **kwargs):
        self.params = kwargs

    def allow(self, subscription):
        """
        Check if the user can run this action

        - Use `self.name` for getting the name of the action
        - Use `self.kwargs` for getting the action parameters

        :param subscription: The user's subscription (marketing.models.PurchasedSubscription) that needs to run the action
        :return: True/False
        """
        raise NotImplemented("Please implement this method")
