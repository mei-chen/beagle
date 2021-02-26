

class UserSettings(object):
    """
    Class designed to handle the operation of getting the user settings.
    Also a good place to define the defaults. Note: these should match with
    the ones defined on the front-end.
    """

    DEFAULTS = {
        'finished_processing_notification': True,
        'collaboration_invite_notification': True,
        'comment_mention_notification': True,
        'owner_changed_notification': True,

        'email_digest_notification': True,
        'default_report_view': '#/widget-panel',
        'include_clause_in_outcoming_mention_emails': True,
    }

    def __init__(self, user):
        self.settings = user.details.settings

    def get_setting(self, setting_name):
        if self.settings and setting_name in self.settings:
            return self.settings[setting_name]
        if setting_name in UserSettings.DEFAULTS:
            return UserSettings.DEFAULTS[setting_name]
