from beagle_simpleapi.endpoint import DetailView, ActionView, ListView
from beagle_simpleapi.mixin import DeleteDetailModelMixin, PostListModelMixin, PutDetailModelMixin
from keywords.models import SearchKeyword
from django.db import IntegrityError


class SearchKeywordDetailView(DetailView, DeleteDetailModelMixin, PutDetailModelMixin):
    model = SearchKeyword
    url_pattern = r'keywords/(?P<keyword>.+)$'
    endpoint_name = 'keyword_detail_view'

    model_key_name = 'keyword'
    url_key_name = 'keyword'

    def get_object(self, request, *args, **kwargs):
        return self.model.objects.get(keyword=self.key_getter(request, *args, **kwargs),
                                      owner=self.user)

    def has_access(self, instance):
        return instance.owner == self.user or self.user.is_superuser


class SearchKeywordActivateActionView(ActionView):
    model = SearchKeyword
    url_pattern = r'keywords/(?P<keyword>.+)/activate$'
    endpoint_name = 'keyword_activate_action_view'

    model_key_name = 'keyword'
    url_key_name = 'keyword'

    def get_object(self, request, *args, **kwargs):
        return self.model.objects.get(keyword=self.key_getter(request, *args, **kwargs),
                                      owner=self.user)

    def has_access(self, instance):
        return instance.owner == self.user or self.user.is_superuser

    def action(self, request, *args, **kwargs):
        self.instance.activate()
        return self.instance.to_dict()


class SearchKeywordDeactivateActionView(ActionView):
    model = SearchKeyword
    url_pattern = r'keywords/(?P<keyword>.+)/deactivate$'
    endpoint_name = 'keyword_deactivate_action_view'

    model_key_name = 'keyword'
    url_key_name = 'keyword'

    def get_object(self, request, *args, **kwargs):
        return self.model.objects.get(keyword=self.key_getter(request, *args, **kwargs),
                                      owner=self.user)

    def has_access(self, instance):
        return instance.owner == self.user or self.user.is_superuser

    def action(self, request, *args, **kwargs):
        self.instance.deactivate()
        return self.instance.to_dict()


class SearchKeywordListView(ListView, PostListModelMixin):
    model = SearchKeyword
    url_pattern = r'keywords/?$'
    endpoint_name = 'keyword_list_view'

    def get_list(self, request, *args, **kwargs):
        return self.model.objects.filter(owner=self.user).order_by('-created')

    def save_model(self, model, item, request, *args, **kwargs):
        model.owner = self.user

        if 'keyword' not in item:
            raise self.BadRequestException("Please specify a 'keyword' field")

        model.keyword = item['keyword']

        if 'active' in item:
            model.active = item['active']

        if 'exact_match' in item:
            model.exact_match = item['exact_match']

        try:
            model.save()
        except IntegrityError:
            raise self.BadRequestException("The keyword is already associated with the user")

        return model
