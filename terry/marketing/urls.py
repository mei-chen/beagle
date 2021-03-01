from django.conf.urls import url, include
from rest_framework import routers

from . import views
from . import viewsets

router = routers.DefaultRouter()
router.register('coupons', viewsets.CouponViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^subscribe',
        views.apply_for_subscription,
        name='purchase_subscription'),
    url(r'^purchase/success$',
        views.payment_return,
        name='payment_return'),
    url(r'^purchase/cancel',
        views.payment_cancel,
        name='payment_cancel')
]
