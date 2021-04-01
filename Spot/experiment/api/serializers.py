import json
import six

# App
from experiment.models import Experiment, Formula

# rest_framework
from rest_framework import serializers


class FormulaSerializerBase(serializers.ModelSerializer):
    class Meta:
        model = Formula
        fields = '__all__'
        read_only_fields = ['uuid']


class FormulaSerializer(FormulaSerializerBase):
    content = serializers.JSONField(
        style={'base_template': 'textarea.html', 'rows': 10}
    )


class FormulaSerializerExtended(FormulaSerializerBase):
    content = serializers.ReadOnlyField(source='content_extended')


class ExperimentSerializerBase(serializers.ModelSerializer):
    # A special annotation for the front-end side
    # (not an actual field, attribute or property)
    is_owner = serializers.BooleanField(read_only=True)

    # A redundant field useful mostly for collaborators
    owner_username = serializers.SerializerMethodField()

    name = serializers.CharField()

    class Meta:
        model = Experiment
        exclude = ['formula', 'owner']
        read_only_fields = ['uuid']

    def get_owner_username(self, obj):
        return obj.owner.username


class FormulaContentExtendedWriteOnlyField(serializers.Field):
    """
    Useful for accessing 'formula.content_extended' simply as 'formula'.
    Needed for creating/updating experiments both via the website or the API
    admin panel (works in a more flexible way than some built-in fields and
    in the API admin panel even visually looks better).
    """

    default_error_messages = {
        'invalid': 'Value must be valid JSON.'
    }

    def to_representation(self, value):
        return json.dumps(value.content_extended, indent=4)

    def to_internal_value(self, data):
        if isinstance(data, six.text_type):
            try:
                data = json.loads(data)
            except:
                self.fail('invalid')
        return data


class ExperimentSerializer(ExperimentSerializerBase):
    formula = FormulaContentExtendedWriteOnlyField(
        help_text='Content',
        style={'base_template': 'textarea.html', 'rows': 10}
    )
    class Meta:
        model = Experiment
        exclude = ['owner']
        read_only_fields = ['uuid']


class ExperimentSerializerExtended(ExperimentSerializerBase):
    formula = FormulaSerializerExtended()

    class Meta:
        model = Experiment
        exclude = ['owner']
        read_only_fields = ['uuid']

    online_learners = serializers.SerializerMethodField()

    @staticmethod
    def online_learner_to_dict(online_learner):
        online_learner_dict = online_learner.to_dict()
        tag = online_learner_dict.pop('tag')
        # Format: <username>#<experiment_uuid>
        username, _, _ = tag.partition('#')
        online_learner_dict['username'] = username
        return online_learner_dict

    def get_online_learners(self, obj):
        return list(map(self.online_learner_to_dict,
                   obj.online_learners.order_by('tag')))
