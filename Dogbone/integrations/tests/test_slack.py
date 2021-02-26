import mock
from dogbone.testing.base import BeagleWebTest
from integrations.tasks import send_slack_message, slack
from django.conf import settings


class SlackbotTest(BeagleWebTest):
    def test_send_slackbot_message(self):
        with mock.patch('integrations.tasks.slack.delay') as mock_slack:
            send_slack_message('message  asdasfd 12341234', '#dev')
            mock_slack.assert_called_with(settings.SLACK_WEBHOOK, 'message  asdasfd 12341234', '#dev')

    def test_slack(self):
        with mock.patch('integrations.slack.requests.post') as mock_post:
            slack(settings.SLACK_WEBHOOK, 'message  asdasfd 12341234', '#dev')
            mock_post.assert_called_with(settings.SLACK_WEBHOOK,
                                         json={
                                             'username': None,
                                             'text': 'message  asdasfd 12341234',
                                             'icon_emoji': None,
                                             'channel': '#dev'
                                         })
