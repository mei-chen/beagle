from marketing.action import Action
from dogbone.app_settings.marketing_settings import WebApplicationSubscription


class WebAction(Action):
    name = 'webapp_action'

    def allow(self, subscription):
        if issubclass(subscription.get_subscription(), WebApplicationSubscription):
            return True
        return False


class ApiUploadAction(Action):
    name = 'api_upload'

    def allow(self, subscription):
        return True


class AppUploadAction(WebAction):
    name = 'app_upload'


class OCRAction(WebAction):
    name = 'ocr'


class InviteAction(WebAction):
    name = 'invite'

    def allow(self, subscription):
        if 'document' not in self.params or self.params['document'].owner != subscription.buyer:
            return False

        return True


class DeleteInviteAction(WebAction):
    name = 'delete_invite'


class ExportAction(WebAction):
    name = 'export'


class CommentAction(WebAction):
    # TODO: A user can comment if he can invite people or if he was invited to the current doc
    name = 'comment'


class EditClauseAction(WebAction):
    name = 'edit_clause'


class AcceptChangesAction(WebAction):
    name = 'accept_changes'


class RejectChangesAction(WebAction):
    name = 'reject_changes'


class LikeAction(WebAction):
    name = 'like'


class DislikeAction(WebAction):
    name = 'dislike'


class AddTagAction(WebAction):
    name = 'add_tag'


class DeleteTagAction(WebAction):
    name = 'delete_tag'
