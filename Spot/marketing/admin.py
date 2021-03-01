from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'use_count', 'is_available']
    readonly_fields = ['created', 'modified']
    search_fields = ['code']
