from django.contrib import admin

from .models import Dataset, DatasetMapping, LabelingTask, Assignment


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner_', 'supervised', 'samples_count',
                    'created']
    readonly_fields = ['samples_count', 'test_percentage', 'uuid', 'created',
                       'modified']
    raw_id_fields = ['owner']

    def owner_(self, obj):
        return obj.owner

    owner_.admin_order_field = 'owner__username'


@admin.register(DatasetMapping)
class DatasetMappingAdmin(admin.ModelAdmin):
    list_display = ['id', 'dataset_', 'created']
    raw_id_fields = ['dataset']

    def dataset_(self, obj):
        return obj.dataset

    dataset_.admin_order_field = 'dataset__name'


@admin.register(LabelingTask)
class LabelingTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner_', 'dataset_', 'created']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['dataset', 'owner']

    def dataset_(self, obj):
        return obj.dataset

    dataset_.admin_order_field = 'dataset__name'

    def owner_(self, obj):
        return obj.owner

    owner_.admin_order_field = 'owner__username'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'labeling_task', 'assignee_', 'score', 'stage',
                    'labeled', 'skipped', 'left', 'total', 'done', 'created']
    readonly_fields = ['stage', 'labeled', 'skipped', 'left', 'total', 'done',
                       'created', 'modified']
    raw_id_fields = ['labeling_task', 'assignee']
    exclude = ['stages_count', 'labeled_samples_count', 'skipped_samples_count']

    def assignee_(self, obj):
        return obj.assignee

    assignee_.admin_order_field = 'assignee__username'

    # Shorter aliases for verbose properties

    def stage(self, obj):
        return obj.stages_count

    def labeled(self, obj):
        return obj.labeled_samples_count

    def skipped(self, obj):
        return obj.skipped_samples_count

    def left(self, obj):
        return obj.left_samples_count

    def total(self, obj):
        return obj.total_samples_count

    def done(self, obj):
        return obj.is_done

    done.boolean = True
