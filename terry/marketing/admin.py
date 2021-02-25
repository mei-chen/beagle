import datetime

from django.contrib import admin
from django.contrib.humanize.templatetags import humanize
from django.utils import timezone

from .models import PurchasedSubscription, Coupon


def extend_timebound_by_days(modeladmin, request, queryset, days):
    for subscription in queryset:
        subscription.expiration_date += datetime.timedelta(days=days)
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
        subscription.expiration_date = timezone.now()
        subscription.save()
end_now.short_description = 'End NOW'


@admin.register(PurchasedSubscription)
class PurchasedSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'coupon_used', 'buyer', 'expires_in', 'active')
    search_fields = ('subscription', 'coupon_used', 'buyer__username', 'buyer__email',
                     'buyer__first_name', 'buyer__last_name')
    actions = [extend_by_7days, extend_by_14days, extend_by_30days, end_now]

    def expires_in(self, obj):
        return humanize.naturalday(obj.expiration_date)

    def active(self, obj):
        return not obj.expired


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'subscription', 'purchase_price', 'is_available', 'use_count']
