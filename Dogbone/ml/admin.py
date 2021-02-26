from django.contrib import admin
from .models import OnlineLearner, PretrainedLearner, LearnerAttribute


class OnlineLearnerAdmin(admin.ModelAdmin):
    list_display = ('tag', 'owner', 'positive_set_size', 'pretrained',
                    'active', 'deleted', 'color_code')
    search_fields = ('tag', 'owner__username', 'owner__email')
    list_filter = ('pretrained', 'active', 'deleted')
    readonly_fields = ('model_uuid', 'model_s3')

admin.site.register(OnlineLearner, OnlineLearnerAdmin)


class PretrainedLearnerAdmin(admin.ModelAdmin):
    list_display = ('tag', 'exclusivity')
    search_fields = ('tag', 'exclusivity')
    readonly_fields = ('model_uuid',)

admin.site.register(PretrainedLearner, PretrainedLearnerAdmin)


class LearnerAttributeAdmin(admin.ModelAdmin):
    list_display = ('tag', 'name', 'output_range')
    search_fields = ('tag', 'name')
    readonly_fields = ('model_uuid',)

admin.site.register(LearnerAttribute, LearnerAttributeAdmin)
