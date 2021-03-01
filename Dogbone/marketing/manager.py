from .models import PurchasedSubscription
from .action import Action


class ActionManager:
    def __init__(self, user):
        self.user = user

        if self.user is None:
            self.subscriptions = []
        else:
            self.subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)

    @property
    def is_valid(self):
        """
        An `ActionManager` is valid if the user is not None.
        If the user is None, it will always return False
        :return:
        """
        return self.user is not None

    def current_subscriptions(self):
        """
        Get the users current subscriptions
        :return:
        """
        return self.subscriptions

    def has_permission(self, action, **kwargs):
        """
        Check if the user can perform a certain action
        For each of the user's subscriptions, check if the subscription satisfies the constraints of the action

        Special parameter: `allow_hooks` a list of function(user) that override the behavior

        :param action: string (the name of the action)
        :param kwargs: parameters of the action
        :return:
        """

        if self.user is None:
            return False

        # Extract the `allow_hooks` from the parameters
        if 'allow_hooks' in kwargs:
            allow_hooks = kwargs.pop('allow_hooks')
        else:
            allow_hooks = []

        # Make the `allow_hooks` a list
        if not isinstance(allow_hooks, list):
            allow_hooks = [allow_hooks]

        # Check the hooks
        for hook in allow_hooks:
            if hook(self.user):
                return True

        action_class = Action.get_action_by_name(action)
        action_object = action_class(**kwargs)

        for subscription in self.subscriptions:
            if action_object.allow(subscription):
                return True

        return False


