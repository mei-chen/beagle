import datetime
from django.contrib import admin
from django.contrib.humanize.templatetags import humanize
from django.utils import timezone
from django.db import models
from .models import Coupon, PurchasedSubscription, PaymentRecord
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import FieldListFilter


class FutureDateFieldListFilter(FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = '%s__' % field_path
        self.date_params = dict([(k, v) for k, v in params.items()
                                 if k.startswith(self.field_generic)])

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any date'), {}),
            (_('Today'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Next 7 days'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(next_month),
            }),
            (_('Next month'), {
                self.lookup_kwarg_since: str(next_month),
                self.lookup_kwarg_until: str(next_month + datetime.timedelta(days=30)),
            }),
            (_('This year'), {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
                self.lookup_kwarg_until: str(next_year),
            }),
        )
        super(FutureDateFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_until]

    def choices(self, cl):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': cl.get_query_string(
                                    param_dict, [self.field_generic]),
                'display': title,
            }


def extend_timebound_by_days(modeladmin, request, queryset, days):
    for subscription in queryset:
        subscription.end += datetime.timedelta(days=days)
        subscription.save()


def extend_by_7days(modeladmin, request, queryset):
    return extend_timebound_by_days(modeladmin, request, queryset, 7)
extend_by_7days.short_description = "Extend by a week"


def extend_by_14days(modeladmin, request, queryset):
    return extend_timebound_by_days(modeladmin, request, queryset, 14)
extend_by_14days.short_description = "Extend by 2 weeks"


def extend_by_30days(modeladmin, request, queryset):
    return extend_timebound_by_days(modeladmin, request, queryset, 30)
extend_by_30days.short_description = "Extend by 30 days"


def end_now(modeladmin, request, queryset):
    for subscription in queryset:
        subscription.end = timezone.now()
        subscription.save()
end_now.short_description = 'End NOW'


class CouponAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('code', 'title', 'start', 'end', 'subscription', 'actual_purchase_price', 'coupon_is_expired')
    search_fields = ('code', 'notes', 'title')
    list_filter = ('start', 'end', 'created')
    actions = [extend_by_7days, extend_by_14days, extend_by_30days, end_now]

    def coupon_is_expired(self, obj):
        return obj.is_expired

    def actual_purchase_price(self, obj):
        return obj.purchase_price


admin.site.register(Coupon, CouponAdmin)


class PurchasedSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'buyer', 'expires_in', 'purchased_on', 'active', 'coupon_used')
    list_filter = ('created', ('end', FutureDateFieldListFilter), 'subscription')
    search_fields = ('subscription', 'buyer__username', 'buyer__email', 'buyer__first_name', 'buyer__last_name')
    actions = [extend_by_7days, extend_by_14days, extend_by_30days, end_now]

    def expires_in(self, obj):
        return humanize.naturalday(obj.end)

    def purchased_on(self, obj):
        return humanize.naturalday(obj.start)

    def active(self, obj):
        return obj.is_active


admin.site.register(PurchasedSubscription, PurchasedSubscriptionAdmin)


class PaymentRecordAdmin(admin.ModelAdmin):
    pass

admin.site.register(PaymentRecord, PaymentRecordAdmin)