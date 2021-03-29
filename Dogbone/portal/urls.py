# Django
from django.conf.urls import url
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

# App
from .generic import RegisterView
from .forms import SimpleRegisterForm
from portal import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^upload$', views.upload, name='upload'),
    url(r'^upload/file$', views.upload_file, name='upload_file'),
    url(r'^login$', views.login, name='login'),
    url(r'^reset-password', views.reset_password, name='reset_password'),
    url(r'^update-password', views.update_password, name='update_password'),

    url(r'^register$', RedirectView.as_view(url=reverse_lazy('signup')), name='register'),
    url(r'^signup$', RegisterView.as_view(template_name='signup.html', form_class=SimpleRegisterForm), name='signup'),

    url(r'^logout$', views.logout, name='logout'),
    url(r'^extension/register', views.register_browser_extension, name='register_browser_extension'),
    url(r'^extension/welcome', views.welcome_browser_extension, name='welcome_browser_extension'),
    url(r'^dashboard$', views.dashboard, name='dashboard'),
    url(r'^getstarted$', views.getstarted, name='getstarted'),
    url(r'^account$', views.account, name='account'),
    url(r'^redeem-coupon', views.redeem_coupon, name='redeem_coupon'),

    url(r'^purchase/route$', views.purchase_route, name='purchase_route'),
    url(r'^purchase/success$', views.payment_return, name='payment_return'),
    url(r'^purchase/cancel', views.payment_cancel, name='payment_cancel'),
    url(r'^purchase/2mo$', views.purchase_2mo_limited_edition,
        name='purchase_2mo_limited_edition_subscription'),
    url(r'^purchase/(?P<subscription_uid>[a-zA-Z0-9\-_]+)$', views.purchase, name='purchase_subscription'),
    url(r'^purchase$', views.purchase, name='purchase'),

    url(r'^report/(?P<uuid>[a-z0-9\-]+)', views.report, name='report'),
    url(r'^summary/(?P<id>\d+)$', views.summary, name='summary'),
    url(r'^summary/details/(?P<id>\d+)$', views.summary_details, name='summary_details'),

    url(r'^account/google_drive_auth_callback$', views.google_drive_auth_callback,
        name='google_drive_auth_callback'),
    url(r'^account/dropbox_auth_callback$', views.dropbox_auth_callback,
        name='dropbox_auth_callback'),
    url(r'^terms_and_conditions$', TemplateView.as_view(template_name='terms_and_condition.html'), name='terms_and_condition'),

    url(r'^spot/authorize/?$', views.spot_authorize, name='spot_authorize'),
    url(r'^kibble/authorize/?$', views.kibble_authorize, name='kibble_authorize'),
]
