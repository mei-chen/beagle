from rest_framework import serializers

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coupon
        fields = (
            'title', 'subscription', 'description', 'is_available', 'purchase_price'
        )
