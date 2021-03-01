# Django
from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView

# App
from .generic import RegisterView
from .forms import SimpleRegisterForm

urlpatterns = patterns(
    '',
    url(r'^$', 'portal.views.index', name='index'),
    url(r'^upload$', 'portal.views.upload', name='upload'),
    url(r'^upload/file$', 'portal.views.upload_file', name='upload_file'),
    url(r'^login$', 'portal.views.login', name='login'),
    url(r'^reset-password', 'portal.views.reset_password', name='reset_password'),
    url(r'^update-password', 'portal.views.update_password', name='update_password'),

    url(r'^register$', RedirectView.as_view(url=reverse_lazy('signup')), name='register'),
    url(r'^signup$', RegisterView.as_view(template_name='signup.html', form_class=SimpleRegisterForm), name='signup'),

    url(r'^logout$', 'portal.views.logout', name='logout'),
    url(r'^extension/register', 'portal.views.register_browser_extension', name='register_browser_extension'),
    url(r'^extension/welcome', 'portal.views.welcome_browser_extension', name='welcome_browser_extension'),
    url(r'^dashboard$', 'portal.views.dashboard', name='dashboard'),
    url(r'^getstarted$', 'portal.views.getstarted', name='getstarted'),
    url(r'^account$', 'portal.views.account', name='account'),
    url(r'^redeem-coupon', 'portal.views.redeem_coupon', name='redeem_coupon'),

    url(r'^purchase/route$', 'portal.views.purchase_route', name='purchase_route'),
    url(r'^purchase/success$', 'portal.views.payment_return', name='payment_return'),
    url(r'^purchase/cancel', 'portal.views.payment_cancel', name='payment_cancel'),
    url(r'^purchase/2mo$', 'portal.views.purchase_2mo_limited_edition',
        name='purchase_2mo_limited_edition_subscription'),
    url(r'^purchase/(?P<subscription_uid>[a-zA-Z0-9\-_]+)$', 'portal.views.purchase', name='purchase_subscription'),
    url(r'^purchase$', 'portal.views.purchase', name='purchase'),

    url(r'^report/(?P<uuid>[a-z0-9\-]+)', 'portal.views.report', name='report'),
    url(r'^summary/(?P<id>\d+)$', 'portal.views.summary', name='summary'),
    url(r'^summary/details/(?P<id>\d+)$', 'portal.views.summary_details', name='summary_details'),

    url(r'^account/google_drive_auth_callback$', 'portal.views.google_drive_auth_callback',
        name='google_drive_auth_callback'),
    url(r'^account/dropbox_auth_callback$', 'portal.views.dropbox_auth_callback',
        name='dropbox_auth_callback'),
    url(r'^terms_and_conditions$', TemplateView.as_view(template_name='terms_and_condition.html'), name='terms_and_condition'),

    url(r'^spot/authorize/?$', 'portal.views.spot_authorize', name='spot_authorize'),
    url(r'^kibble/authorize/?$', 'portal.views.kibble_authorize', name='kibble_authorize'),
)
