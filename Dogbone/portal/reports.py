import pytz
from django_reports import Report
from django.contrib.auth.models import User
from django.utils.timezone import now
from django import forms
from core.models import Document
from datetime import datetime
from dateutil.relativedelta import relativedelta


class UserDocumentUploadReport(Report):

    # Starting from 0
    sort_by_column = 3
    form_class = None
    description = 'The number of documents each user uploaded'

    def generate(self, **kwargs):
        users = User.objects.all()

        yield ('ID', 'EMAIL', 'USERNAME', 'DOCUMENT_COUNT')

        for user in users:
            yield (user.pk, user.email, user.username, Document.lightweight.filter(owner=user).count())


class MostActiveUsersForm(forms.Form):
    best_count = forms.IntegerField(min_value=1)


class MostActiveUsers(Report):

    # Starting from 0
    sort_by_column = None

    form_class = MostActiveUsersForm
    description = 'The Most Active users report'

    def generate(self, **kwargs):
        user_count = int(kwargs['best_count'][0]) if isinstance(kwargs['best_count'], list) else int(kwargs['best_count'])
        users = User.objects.all()
        users = sorted(users, key=lambda u: Document.lightweight.filter(owner=u).count(), reverse=True)[:user_count]

        yield ('ID', 'EMAIL', 'USERNAME', 'DOCUMENT_COUNT')

        for user in users:
            yield (user.pk, user.email, user.username, Document.lightweight.filter(owner=user).count())


class UserCountByMonth(Report):

    # Starting from 0
    sort_by_column = None

    form_class = None
    description = 'User count, aggregated by month'

    def localize(self, dt):
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = pytz.utc.localize(dt)

        return dt

    def generate(self, **kwargs):
        one_month = relativedelta(months=+1)

        # Get the oldest user
        first_user = User.objects.all().earliest('date_joined')

        # Get the first month
        first_joined = first_user.date_joined
        first_month = datetime(year=first_joined.year, month=first_joined.month, day=1)
        first_month = self.localize(first_month)

        current_month = first_month
        prev_count = 0

        yield ('MONTH', 'USER_COUNT', 'DIFFERENCE', )

        while current_month <= now():
            user_count = User.objects.filter(date_joined__lte=current_month).count()
            user_delta = user_count - prev_count

            yield (str(current_month.date()), user_count,
                   ('-' if user_delta < 0 else '+') + str(user_delta))

            prev_count = user_count
            current_month = current_month + one_month
