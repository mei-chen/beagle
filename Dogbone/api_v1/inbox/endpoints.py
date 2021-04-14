import json
from notifications.models import Notification
from django.contrib.auth.models import User
from beagle_simpleapi.endpoint import ListView, DetailView, ActionView
from beagle_simpleapi.mixin import PutDetailModelMixin
from core.tools import notification_to_dict, notification_url
from core.tasks import fully_refresh_persistent_notifications


class InboxListView(ListView):
    model = Notification
    url_pattern = r'user/me/inbox'
    endpoint_name = 'inbox_list_view'

    DEFAULT_RESULTS_PER_PAGE = 20

    @classmethod
    def to_dict(cls, model):
        return notification_to_dict(model)

    @staticmethod
    def get_url(model):
        return notification_url(model)

    def get_page_count(self):
        rpp = self.get_rpp()
        object_count = self.get_object_count()
        return self._compute_page_count(object_count, rpp)

    def get_object_count(self):
        return self.user.notifications.all().count()

    def get_unread_count(self):
        return self.user.notifications.unread().count()

    def meta(self):
        return {'pagination': self.pagination(),
                'unread_count': self.get_unread_count()}

    def wrap_result(self, result):
        return {'objects': result,
                'meta': self.meta()}

    def get_list(self, request, *args, **kwargs):
        if request.GET.get('read', False):
            qs = self.user.notifications.read()
        elif request.GET.get('unread', False):
            qs = self.user.notifications.unread()
        else:
            qs = self.user.notifications.all()

        return qs[self.get_slice()]


class InboxDetailView(DetailView, PutDetailModelMixin):
    model = Notification
    url_pattern = r'user/me/inbox/(?P<id>[0-9]+)'
    endpoint_name = 'inbox_detail_view'

    @classmethod
    def to_dict(cls, model):
        return notification_to_dict(model)

    def get_object(self, request, *args, **kwargs):
        try:
            return self.user.notifications.get(pk=int(kwargs['id']))
        except ValueError:
            raise self.BadRequestException("Please provided a valid notification id")
        except Notification.DoesNotExist:
            raise self.NotFoundException("This notification does not exist")

    def save_model(self, model, data, request, *args, **kwargs):
        if ('read' in data and data['read']) or ('unread' in data and not data['unread']):
            model.mark_as_read()

        if ('read' in data and not data['read']) or ('unread' in data and data['unread']):
            model.mark_as_unread()

        return model


class InboxMarkAllView(ActionView):
    model = User
    url_pattern = r'user/me/inbox/mark_all'
    endpoint_name = 'inbox_mark_all_view'

    def get_object(self, request, *args, **kwargs):
        return request.user

    def has_access(self, instance):
        return True

    def action(self, request, *args, **kwargs):
        request_data = json.loads(request.body)

        if request_data.get('read'):
            self.user.notifications.all().mark_all_as_read()
            fully_refresh_persistent_notifications.delay(self.user.id)
        elif request_data.get('unread'):
            self.user.notifications.all().mark_all_as_unread()

        return {'status': 1, 'message': "OK"}
