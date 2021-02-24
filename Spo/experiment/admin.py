from django.contrib import admin

from .models import (
    Experiment,
    Formula,
    RegexClassifier,
    BuiltInClassifier,
    TrainedClassifier,
    ExperimentAttribute,
)


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner_', 'public', 'uuid', 'created']
    readonly_fields = ['uuid', 'created', 'modified']
    raw_id_fields = ['formula', 'owner']
    search_fields = ['name', 'owner__username', 'uuid']

    def owner_(self, obj):
        return obj.owner

    owner_.admin_order_field = 'owner__username'


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ['id', 'experiment_', 'uuid', 'created']
    readonly_fields = ['uuid', 'created', 'modified']
    search_fields = ['uuid'] + [
        'experiment__%s' % field for field in ExperimentAdmin.search_fields
    ]

    def experiment_(self, obj):
        return obj.experiment

    experiment_.admin_order_field = 'experiment__name'


class GenericClassifierAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'reverse', 'created']
    readonly_fields = ['clf_type', 'uuid', 'created', 'modified']
    search_fields = ['uuid']


@admin.register(RegexClassifier)
class RegexClassifierAdmin(GenericClassifierAdmin):
    pass


@admin.register(BuiltInClassifier)
class BuiltInClassifierAdmin(GenericClassifierAdmin):
    pass


@admin.register(TrainedClassifier)
class TrainedClassifierAdmin(GenericClassifierAdmin):
    raw_id_fields = ['datasets']


@admin.register(ExperimentAttribute)
class ExperimentAttributeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parent', 'child', 'created']
    raw_id_fields = ['parent', 'child']
    readonly_fields = ['created', 'modified']
