from rest_framework import viewsets, mixins

from .models import Coupon
from .serializers import CouponSerializer


class CouponViewSet(mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    """
    API endpoint that allows coupons to be viewed.
    """

    queryset = Coupon.objects.all()
    lookup_field = 'code'
    serializer_class = CouponSerializer
