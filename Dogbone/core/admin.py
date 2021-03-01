from django.contrib import admin
from .models import (
    Document,
    CollaborationInvite,
    Sentence,
    ExternalInvite,
    DelayedNotification,
    CollaboratorList,
    Batch,
)
from .tasks import process_document_task
from integrations.models import GeneralLog, SpecialLog
from utils.django_utils.admin_utils import DeleteWithoutConfirmationAdminMixin


def force_reanalysis(modeladmin, request, queryset):
    for document in queryset:
        document.doclevel_analysis = None
        document.pending = True
        document.save()

        # Trigger an analysis task
        process_document_task.delay(document.pk, doclevel=True, is_reanalisys=True)

force_reanalysis.short_description = "Force document reanalysis"


class DocumentAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('title', 'owner', 'is_ready', 'created', 'uuid_', 'agreement_type', 'upload_source')
    readonly_fields = ('uuid_', 'cached_analysis')
    search_fields = ('original_name', 'title', 'uuid', 'owner__username', 'owner__email')
    list_filter = ('pending', 'created', 'agreement_type', 'upload_source')
    raw_id_fields = ('owner', 'batch')
    exclude = ('uuid',)
    actions = [force_reanalysis]

    def uuid_(self, obj):
        """ Makes UUID field a clickable link to report page. """

        return '<a href="%s" target="_blank">%s</a>' % (obj.get_report_url(), obj.uuid)

    uuid_.allow_tags = True
    uuid_.short_description = 'UUID'

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """

        qs = self.model.lightweight.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    # For single object retrieve original (not deferred one)
    # so all Document methods and signals will be intact
    def get_object(self, request, object_id):
        try:
            return Document.objects.get(pk=object_id)
        except Document.DoesNotExist:
            return None

    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified',)
        super(DocumentAdmin, self).__init__(*args, **kwargs)


admin.site.register(Document, DocumentAdmin)


class SentenceAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('pk', 'document_title', 'document_uuid', 'accepted', 'rejected', )
    list_filter = ('created', )
    search_fields = ('doc__title', 'doc__uuid', 'uuid')
    raw_id_fields = ("doc", "prev_revision", "lock", )

    def document_title(self, obj):
        return obj.doc.title

    def document_uuid(self, obj):
        return obj.doc.uuid


admin.site.register(Sentence, SentenceAdmin)


class CollaborationInviteAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('document_title', 'inviter', 'invitee', 'inviter_email', 'invitee_email', 'created',)
    list_filter = ('created', )
    search_fields = ('document__title', 'document__uuid',
                     'inviter__username', 'invitee__username',
                     'inviter__email', 'invitee__email')

    def document_title(self, obj):
        return obj.document.title

    def inviter_email(self, obj):
        return obj.inviter.email

    def invitee_email(self, obj):
        return obj.invitee.email


admin.site.register(CollaborationInvite, CollaborationInviteAdmin)


class ExternalInviteAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('document_title', 'inviter', 'email', 'inviter_email',
                    'pending', 'created')
    list_filter = ('created',)
    search_fields = ('document__title', 'document__uuid',
                     'inviter__username', 'inviter__email', 'email')

    def document_title(self, obj):
        return obj.document.title

    def inviter_email(self, obj):
        return obj.inviter.email


admin.site.register(ExternalInvite, ExternalInviteAdmin)


class DelayedNotificationAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_filter = ('created', )
    list_display = ('__unicode__', 'email', 'created',)


admin.site.register(DelayedNotification, DelayedNotificationAdmin)


class CollaboratorListAdmin(admin.ModelAdmin):
    list_per_page = 20


admin.site.register(CollaboratorList, CollaboratorListAdmin)


class SpecialLogAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('level', 'time', 'message')
    search_fields = ['message']


admin.site.register(SpecialLog, SpecialLogAdmin)


class GeneralLogAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('level', 'time', 'message')
    search_fields = ['message']


admin.site.register(GeneralLog, GeneralLogAdmin)


class BatchAdmin(DeleteWithoutConfirmationAdminMixin, admin.ModelAdmin):
    list_per_page = 20
    list_display = ('name', 'documents_count', 'owner', 'is_analyzed', 'created')
    readonly_fields = ('invalid_docs', 'documents_count', 'is_analyzed', 'created', 'modified')
    raw_id_fields = ('owner',)
    search_fields = ('name', 'owner__username', 'owner__email')


admin.site.register(Batch, BatchAdmin)
