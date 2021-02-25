from rest_framework import serializers

from document.models import Document, Sentence, PersonalData, CustomPersonalData
from portal.models import File


class DocumentSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='document-detail'
    )
    has_sentences = serializers.BooleanField()
    cleaned_txt = serializers.ReadOnlyField(source='cleaned_txt_url')
    cleaned_docx = serializers.ReadOnlyField(source='cleaned_docx_url')

    class Meta:
        model = Document
        fields = '__all__'


class ConvertSerializer(serializers.Serializer):
    files = serializers.PrimaryKeyRelatedField(
        many=True, queryset=File.objects.all())

    class Meta:
        fields = '__all__'


class CleanupDocumentSerializer(serializers.Serializer):
    sequence = serializers.ListField(
        child=serializers.CharField()
    )
    documents = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Document.objects.all())

    def validate_sequence(self, value):
        missing = [tool for tool in value if tool not in Document.get_tool()]
        if missing:
            raise serializers.ValidationError(
                "No such tools {}".format(missing))
        return value

    class Meta:
        fields = '__all__'


class CleanupDocumentToolsSerializer(serializers.Serializer):
    tool = serializers.CharField()

    class Meta:
        fields = '__all__'


class SentenceCreateSerializer(serializers.ModelSerializer):
    documents = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), many=True
    )

    class Meta:
        model = Sentence
        fields = ('documents',)


class PersonalDataSerializer(serializers.ModelSerializer):
    batch = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    @staticmethod
    def get_batch(obj):
        return obj.batch.name

    @staticmethod
    def get_document(obj):
        return obj.document.name

    class Meta:
        model = PersonalData
        fields = '__all__'


class CustomPersonalDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomPersonalData
        fields = '__all__'
