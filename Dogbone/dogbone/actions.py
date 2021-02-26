from core.models import CollaborationInvite

# Users with a proper subscription can perform these actions
SUBSCRIPTION_BASED_ACTIONS = (
    'api_upload',
    'app_upload',
    'export',
    'delete_invite',
    'accept_changes',
    'reject_changes'
)

# Users can perform these actions even if they don't have a subscription, just invited to a document
INVITATION_BASED_ACTIONS = (
    'like',
    'dislike',
    'add_tag',
    'delete_tag',
    'comment'
)

OWNER_ONLY_BASED_ACTIONS = (
    'invite',
)


def has_permission(request, action_name, **kwargs):
    """
    Handy shortcut for checking if a user is allowed to do a certain action
    :param request: The request object with the attached `action_manager`
    :param action_name: The name of the action that is wanted to be executed
    :param kwargs: Params needed to make the decision
    :return: tuple(allow, message)
    """

    try:
        request.action_manager
    except AttributeError:
        return False, 'The request object is missing the ActionManager'

    kwargs['allow_hooks'] = [lambda u: u.is_superuser]
    document = kwargs.get('document', None)

    IS_OWNER = lambda u: document.owner == u
    IS_INVITED = lambda u: CollaborationInvite.objects.filter(invitee=u, document=document).exists()

    if (action_name in INVITATION_BASED_ACTIONS or action_name in OWNER_ONLY_BASED_ACTIONS) and document is None:
        return False, 'Please provide a document object'

    # Depends if the user has access to the document
    if action_name in INVITATION_BASED_ACTIONS:
        kwargs['allow_hooks'].extend([IS_INVITED, IS_OWNER])

    # Depends if the user is the owner
    elif action_name in OWNER_ONLY_BASED_ACTIONS:
        kwargs['allow_hooks'].extend([IS_OWNER])

    allow = request.action_manager.has_permission(action_name, **kwargs)

    if not allow:
        message = 'Check the parameters provided and your current subscription'
    else:
        message = 'Action allowed'

    return allow, message