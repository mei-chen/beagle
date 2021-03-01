from django import forms
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from longerusernameandemail.admin import LongerUsernameAndEmailUserAdmin

from core.models import Document
from marketing.models import PurchasedSubscription
from portal.models import UserProfile, WrongAnalysisFlag, PDFUploadMonitor
from utils.django_utils.admin_utils import DeleteWithoutConfirmationAdminMixin


def reset_initialtour(modeladmin, request, queryset):
    for userprofile in queryset:
        userprofile.initial_tour = None
        userprofile.save()
reset_initialtour.short_description = "Force initial tour reset"


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_display = ('user', 'user_username', 'user_email', 'job_title', 'document_upload_count')
    actions = [reset_initialtour]

    def user_email(self, obj):
        return obj.user.email

    def user_username(self, obj):
        return obj.user.username


class PDFUploadMonitorAdmin(admin.ModelAdmin):
    pass


class WrongAnalysisFlagAdmin(admin.ModelAdmin):
    pass


class UserCreationWithEmailForm(UserCreationForm):
    """ A form that creates a user, with no privileges, from the given username, email and password. """
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(label=_("Username"), max_length=300,
                                regex=r'^[\w.@+-]+$',
                                help_text=_("Required. 300 characters or fewer. Letters, digits and @/./+/-/_ only."),
                                error_messages={
                                    'invalid': _(
                                        "This value may contain only letters, numbers and @/./+/-/_ characters.")
                                })
    email = forms.EmailField(label=_("Email"), max_length=300,
                             help_text=_("Required. 300 characters or fewer. Proper email format."))

    class Meta:
        model = User
        fields = ("username", "email", )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        try:
            User._default_manager.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(
            self.error_messages['duplicate_email'],
            code='duplicate_email',
        )


class UserProfileInlineForm(forms.ModelForm):
    phone = forms.CharField(widget=forms.TextInput, required=False)
    job_title = forms.CharField(widget=forms.TextInput, required=False)
    company = forms.CharField(widget=forms.TextInput, required=False)

    class Meta:
        model = UserProfile


class UserProfileAdminInline(admin.StackedInline):
    form = UserProfileInlineForm
    model = UserProfile
    exclude = ('avatar', 'avatar_s3', 'tags_cache', 'keywords_cache')
    can_delete = False
    readonly_fields = ['document_upload_count', 'initial_tour']


class SubscriptionsAdminInline(admin.TabularInline):
    model = PurchasedSubscription
    extra = 0


class DocumentAdminInline(admin.TabularInline):
    model = Document
    extra = 0
    can_delete = False
    editable_fields = []
    readonly_fields = []
    exclude = ['initsample', 'sents', 'docx_s3', 'pdf_s3', 'cached_analysis', 'doclevel_analysis', 'dirty', 'docx_file']

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in self.model._meta.fields
                if field.name not in self.editable_fields and
                   field.name not in self.exclude]

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super(DocumentAdminInline, self).get_queryset(request)
        return qs.order_by('-created')


class UserExtendedAdmin(DeleteWithoutConfirmationAdminMixin, LongerUsernameAndEmailUserAdmin):
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2')}
        ),
    )
    add_form = UserCreationWithEmailForm
    list_display = ('email', 'username', 'first_name', 'last_name',
                    'last_login', 'is_active', 'date_joined', 'is_staff')
    ordering = ('-is_active', '-date_joined')
    inlines = ()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = (UserProfileAdminInline, SubscriptionsAdminInline, DocumentAdminInline)
        return super(UserExtendedAdmin, self).change_view(request, object_id)

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = ()
        return super(UserExtendedAdmin, self).add_view(request)

    def delete_model(self, request, obj):
        # Make sure to also delete (more precisely, mark them as trash)
        # all owned documents (delete documents one by one, don't do a bulk
        # delete, since it won't call the overridden Document.delete method)
        for document in obj.document_set.all():
            document.delete()

        obj.is_active = False

        # Inactive users can't log in to the website, but only after they
        # log out, so make sure to also delete all associated sessions
        obj.session_set.all().delete()

        obj.save()


admin.site.unregister(User)
admin.site.register(User, UserExtendedAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(PDFUploadMonitor, PDFUploadMonitorAdmin)
admin.site.register(WrongAnalysisFlag, WrongAnalysisFlagAdmin)
