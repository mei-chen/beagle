from django import forms
from django.contrib.auth.models import User

from django_reports import Report
from statistics.models import Event


class ViewsUsageForm(forms.Form):
    username = forms.CharField(
        required=False,
        label='Username (or leave blank to get report for all users)'
    )


class ViewsUsageReport(Report):

    # Starting from 0
    sort_by_column = None

    form_class = ViewsUsageForm
    description = 'Events count report'

    def generate(self, **kwargs):
        username = (kwargs['username'][0]
                    if isinstance(kwargs['username'], list)
                    else kwargs['username'])

        events_qs = Event.objects.all()

        if username:
            user = User.objects.get(username=username)
            events_qs = events_qs.filter(user=user)

        events_counts = {
            'widget': events_qs.filter(name='open_widget_view').count(),
            'context': events_qs.filter(name='open_context_view').count(),
            'detail': events_qs.filter(name='open_detail_view').count(),
            'clause': events_qs.filter(name='open_clause_view').count()
        }

        yield ('VIEW', 'HITS')

        for event, count in events_counts.items():
            yield (event, count)
