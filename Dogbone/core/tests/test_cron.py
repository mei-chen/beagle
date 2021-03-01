import mock
from dogbone.testing.base import BeagleWebTest
from core.tasks import store_activity_notification
from core.cron import periodic_send_notification_reminders
from datetime import datetime, timedelta
from notifications.models import Notification


class TestPeriodicSendNotificationReminders(BeagleWebTest):
    def test_task(self):
        other_user = self.create_user('ivanov.george.bogdan@gmail.com', 'ivanov.g', 'lambada')
        document = self.create_document('SomeImportantDoc', owner=self.user, pending=False)

        notif1_pk = store_activity_notification(actor=self.user,
                                             recipient=self.user,
                                             verb='did',
                                             target=other_user,
                                             action_object=document,
                                             render_string="(actor) did something to (target) using (action_object)",
                                             created=datetime.now() - timedelta(minutes=20))

        notif2_pk = store_activity_notification(actor=self.user,
                                             recipient=other_user,
                                             verb='did',
                                             target=other_user,
                                             action_object=document,
                                             render_string="(actor) did something to (target) using (action_object)",
                                             created=datetime.now() - timedelta(minutes=20))

        notif1 = Notification.objects.get(pk=notif1_pk)
        notif2 = Notification.objects.get(pk=notif2_pk)

        with mock.patch('portal.mailer.BeagleMailer.notification_reminders') as mock_notification_reminders:
            periodic_send_notification_reminders()
            mock_notification_reminders.assert_called_once_with(other_user, [notif2])

    def test_task_no_notifications(self):

        with mock.patch('portal.mailer.BeagleMailer.notification_reminders') as mock_notification_reminders:
            periodic_send_notification_reminders()
            self.assertFalse(mock_notification_reminders.called)

    def test_task_called_multiple_times(self):
        other_user = self.create_user('ivanov.george.bogdan@gmail.com', 'ivanov.g', 'lambada')
        self.make_paid(other_user)
        document = self.create_document('SomeImportantDoc', owner=self.user, pending=False)

        notif1_pk = store_activity_notification(actor=self.user,
                                             recipient=self.user,
                                             verb='did',
                                             target=other_user,
                                             action_object=document,
                                             render_string="(actor) did something to (target) using (action_object)",
                                             created=datetime.now() - timedelta(minutes=20))

        notif2_pk = store_activity_notification(actor=self.user,
                                             recipient=other_user,
                                             verb='did',
                                             target=other_user,
                                             action_object=document,
                                             render_string="(actor) did something to (target) using (action_object)",
                                             created=datetime.now() - timedelta(minutes=20))

        notif3_pk = store_activity_notification(actor=self.user,
                                             recipient=other_user,
                                             verb='did',
                                             target=other_user,
                                             action_object=document,
                                             render_string="(actor) did something to (target) using (action_object)",
                                             created=datetime.now() - timedelta(minutes=20))

        notif4_pk = store_activity_notification(actor=other_user,
                                             recipient=self.user,
                                             verb='did',
                                             target=other_user,
                                             action_object=document,
                                             render_string="(actor) did something to (target) using (action_object)",
                                             created=datetime.now() - timedelta(minutes=20))

        notif1 = Notification.objects.get(pk=notif1_pk)
        notif2 = Notification.objects.get(pk=notif2_pk)
        notif3 = Notification.objects.get(pk=notif3_pk)
        notif4 = Notification.objects.get(pk=notif4_pk)

        with mock.patch('portal.mailer.BeagleMailer.notification_reminders') as mock_notification_reminders:
            periodic_send_notification_reminders()
            self.assertEqual(mock_notification_reminders.call_count, 2)

            # Just to be sure the order is irrelevant
            try:
                mock_notification_reminders.assert_has_calls([mock.call(other_user, [notif3, notif2]),
                                                              mock.call(self.user, [notif4])])
            except AssertionError:
                mock_notification_reminders.assert_has_calls([mock.call(self.user, [notif4]),
                                                              mock.call(other_user, [notif3, notif2])])