from beagle_simpleapi.endpoint import DetailView, ListView
from clauses_statistics.models import ClausesStatistic


class ClausesStatisticDetailView(DetailView):
    model = ClausesStatistic
    url_pattern = r'/clauses_statistics/(?P<tag>[^/]+)$'
    endpoint_name = 'clauses_statistic_detail_view'

    model_key_name = 'tag'
    url_key_name = 'tag'


class ClausesStatisticListView(ListView):
    model = ClausesStatistic
    url_pattern = r'/clauses_statistics$'
    endpoint_name = 'clauses_statistic_list_view'
