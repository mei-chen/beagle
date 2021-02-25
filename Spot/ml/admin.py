from django import forms
from django.contrib import admin

from ml.models import OnlineLearner, OnlineDataset, PretrainedLearner, LearnerAttribute


class OnlineLearnerForm(forms.ModelForm):
    class Meta:
        model = OnlineLearner
        fields = '__all__'

    def clean(self):
        super(OnlineLearnerForm, self).clean()

        owner = self.cleaned_data.get('owner')
        experiment = self.cleaned_data.get('experiment')
        if owner and experiment and owner != experiment.owner:
            raise forms.ValidationError(
                'The online learner and the experiment must have the same owner!'
            )


class OnlineLearnerAdmin(admin.ModelAdmin):
    form = OnlineLearnerForm

    list_display = ['tag', 'owner_', 'positive_set_size', 'pretrained', 'active', 'deleted', 'is_mature_']
    search_fields = ['tag', 'owner__username', 'owner__email']
    list_filter = ['pretrained', 'active', 'deleted']
    raw_id_fields = ['owner', 'experiment', 'dataset']
    readonly_fields = ['uuid', 'model_s3']

    def owner_(self, obj):
        return obj.owner

    owner_.admin_order_field = 'owner__username'

    def is_mature_(self, obj):
        return obj.is_mature

    is_mature_.boolean = True

admin.site.register(OnlineLearner, OnlineLearnerAdmin)


class OnlineDatasetAdmin(admin.ModelAdmin):
    list_display = ['learner', 'positive_set_size', 'negative_set_size', 'total_set_size']
    search_fields = ['learner__%s' % field for field in OnlineLearnerAdmin.search_fields]
    readonly_fields = ['uuid']

admin.site.register(OnlineDataset, OnlineDatasetAdmin)


class PretrainedLearnerAdmin(admin.ModelAdmin):
    list_display = ['tag', 'model_type']
    search_fields = ['tag', 'model_type']
    readonly_fields = ['uuid', 'model_s3', 'vectorizer_s3']

admin.site.register(PretrainedLearner, PretrainedLearnerAdmin)


class LearnerAttributeAdmin(admin.ModelAdmin):
    list_display = ['tag', 'name', 'output_range']
    search_fields = ['tag', 'name']
    readonly_fields = ['uuid', 'model_s3', 'vectorizer_s3']

admin.site.register(LearnerAttribute, LearnerAttributeAdmin)
