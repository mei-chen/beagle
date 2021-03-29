from django.contrib import messages
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db import transaction
from django.http.response import HttpResponseRedirect, Http404
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _


class DeleteWithoutConfirmationAdminMixin(object):
    """
    Make sure to place this class in a list of parents before any subclass of
    `django.contrib.admin.ModelAdmin` class in order to use the overridden
    `delete_view` method defined below.
    """

    actions = ['delete_selected']

    @csrf_protect_m
    @transaction.atomic
    def delete_view(self, request, object_id, message=True, **kwargs):
        """
        Deletes an object without any confirmation and without fetching from
        the database and rendering to a web page all the related objects
        which also will be deleted along with the target object.

        Copied from the django source and edited properly.
        """

        opts = self.model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.') %
                {'name': force_text(opts.verbose_name),
                 'key': escape(object_id)}
            )

        obj_display = force_text(obj)
        self.log_deletion(request, obj, obj_display)
        self.delete_model(request, obj)

        if message:
            self.message_user(
                request,
                _('The %(name)s "%(obj)s" was deleted successfully.') % {
                    'name': force_text(opts.verbose_name),
                    'obj': force_text(obj_display)
                },
                messages.SUCCESS
            )

        if self.has_change_permission(request, None):
            url = reverse('admin:%s_%s_changelist' %
                          (opts.app_label, opts.model_name),
                          current_app=self.admin_site.name)
            preserved_filters = self.get_preserved_filters(request)
            url = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts},
                url
            )
        else:
            url = reverse('admin:index',
                          current_app=self.admin_site.name)

        return HttpResponseRedirect(url)

    def delete_selected(self, request, qs):
        count = qs.count()

        for obj in qs.all():
            self.delete_view(request, str(obj.id), message=False)

        opts = self.model._meta

        self.message_user(
            request,
            _('%(count)d %(name)s %(verb)s deleted successfully.') % {
                'count': count,
                'name': force_text(opts.verbose_name
                                   if count == 1 else
                                   opts.verbose_name_plural),
                'verb': 'was' if count == 1 else 'were'
            },
            messages.SUCCESS
        )
