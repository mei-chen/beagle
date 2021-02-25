from collections import Counter

# App
from dataset.models import Dataset, LabelingTask, Assignment

# Django
from django.contrib.auth.models import User

# REST framework
from rest_framework import serializers


class DatasetSerializer(serializers.ModelSerializer):
    # A special annotation for the front-end side
    # (not an actual field, attribute or property)
    is_owner = serializers.BooleanField(read_only=True)

    # A redundant field useful mostly for collaborators
    owner_username = serializers.SerializerMethodField()

    name = serializers.CharField()
    description = serializers.CharField(
        style={'base_template': 'textarea.html'},
        required=False
    )
    klasses = serializers.JSONField()
    supervised = serializers.BooleanField(initial=True)
    # There is a separate API for fetching samples, so serialize
    # here only their count and nothing else
    samples = serializers.ReadOnlyField(source='samples_count')

    # A utility field available only inside the details of a supervised dataset
    samples_per_klass = serializers.SerializerMethodField()

    class Meta:
        model = Dataset
        read_only_fields = ['uuid']
        exclude = ['samples', 'samples_count']

    def get_owner_username(self, obj):
        return obj.owner.username

    def get_samples_per_klass(self, obj):
        samples_counts_per_klass = None
        if obj.supervised and hasattr(obj, 'samples'):
            samples_counts_per_klass = Counter(obj.klass_labels)
        return samples_counts_per_klass

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super(DatasetSerializer, self).create(validated_data)


def get_serializer_class(dataset=None):
    """ Generates a dataset-specific sample serializer class. """

    class_name = 'SampleSerializer%s' % (dataset.pk if dataset else '')
    class_parents = (serializers.Serializer,)

    text_field = serializers.CharField(
        style={'base_template': 'textarea.html'},
        required=False
    )
    label_field = serializers.ChoiceField(
        style={'base_template': 'select.html'},
        choices=dataset.klasses,
        required=False
    ) if dataset and dataset.supervised else None
    dataset_field = serializers.IntegerField(read_only=True)
    index_field = serializers.IntegerField(read_only=True)

    class_attrs = {'text': text_field,
                   'label': label_field,
                   'dataset': dataset_field,
                   'index': index_field}

    return type(class_name, class_parents, class_attrs)


class LabelingTaskSerializerInput(serializers.ModelSerializer):
    assignees = serializers.JSONField(write_only=True, required=False)
    samples = serializers.JSONField(  # evaluation set
        write_only=True, style={'base_template': 'textarea.html'}
    )

    class Meta:
        model = LabelingTask
        exclude = ['evaluation_set']

    def validate(self, data):
        dataset = data['dataset']
        owner = data['owner']

        user = self.context['request'].user

        if not (user == owner or user.is_superuser):
            raise serializers.ValidationError(
                'Cannot create labeling tasks for other users.'
            )

        if not dataset.has_access(owner):
            raise serializers.ValidationError(
                'Owner does not have access to dataset.'
            )

        return data

    def save(self, **kwargs):
        assignees = User.objects.filter(
            id__in=self.validated_data.pop('assignees', [])
        )

        samples = self.validated_data.pop('samples')

        labeling_task = super(LabelingTaskSerializerInput, self).save(**kwargs)

        for assignee in assignees:
            if labeling_task.dataset.has_access(assignee):
                Assignment.objects.get_or_create(
                    labeling_task=labeling_task, assignee=assignee
                )

        try:
            labeling_task.initialize_evaluation_set(samples)
        except:
            labeling_task.delete()
            raise serializers.ValidationError('Invalid evaluation set.')

        return labeling_task


class AssignmentSerializerInput(serializers.ModelSerializer):

    class Meta:
        model = Assignment
        exclude = ['stages', 'stages_count', 'labeled_samples_count']

    def validate(self, data):
        labeling_task = data['labeling_task']
        assignee = data['assignee']

        user = self.context['request'].user

        if not (user == labeling_task.owner or user.is_superuser):
            raise serializers.ValidationError(
                'Cannot assign other users to labeling task.'
            )

        if not labeling_task.dataset.has_access(assignee):
            raise serializers.ValidationError(
                'Assignee does not have access to dataset.'
            )

        if Assignment.objects.filter(
            labeling_task=labeling_task, assignee=assignee
        ).exists():
            raise serializers.ValidationError('Assignment already exists.')

        return data


class DatasetSerializerOutputSimple(serializers.ModelSerializer):
    samples = serializers.ReadOnlyField(source='samples_count')

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'samples']


class UserSerializerOutputSimple(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'username']


class LabelingTaskSerializerOutputSimple(serializers.ModelSerializer):

    class Meta:
        model = LabelingTask
        fields = ['id', 'name', 'description']


class AssignmentSerializerOutputSimple(serializers.ModelSerializer):
    dataset = DatasetSerializerOutputSimple()
    owner = UserSerializerOutputSimple()

    assignee = UserSerializerOutputSimple()

    stats = serializers.ReadOnlyField(source='progress')

    class Meta:
        model = Assignment
        exclude = ['stages', 'stages_count', 'labeled_samples_count',
                   'skipped_samples_count', 'labeling_task']


class LabelingTaskSerializerOutput(LabelingTaskSerializerOutputSimple):
    dataset = DatasetSerializerOutputSimple()
    owner = UserSerializerOutputSimple()

    assignments = AssignmentSerializerOutputSimple(many=True)

    class Meta:
        model = LabelingTask
        exclude = ['evaluation_set']


class AssignmentSerializerOutput(AssignmentSerializerOutputSimple):
    labeling_task = LabelingTaskSerializerOutputSimple()

    class Meta:
        model = Assignment
        exclude = ['stages', 'stages_count', 'labeled_samples_count',
                   'skipped_samples_count', 'labeling_task', 'score']
