import logging

from rest_framework import serializers
from rest_framework.exceptions import APIException

from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import filesizeformat

from portal.models import (
    Profile, File, Batch, Project, KeywordList, ProjectArchive
)

log = logging.getLogger(__name__)


class FileTypeNotSupported(APIException):
    status_code = 400
    default_detail = 'File type is not supported.'
    default_code = 'bad_request'


class BatchUriSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='batch-detail'
    )

    class Meta:
        model = Batch
        fields = (
            'resource_uri', 'id'
        )


class ProfileSerialzer(serializers.ModelSerializer):
    auto_cleanup_tools = serializers.JSONField()
    personal_data_types = serializers.JSONField()
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('user',)


class UserSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='user-detail'
    )
    profile = ProfileSerialzer()

    class Meta:
        model = User
        fields = '__all__'


class KeywordListUriSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='keywordlist-detail'
    )

    class Meta:
        model = KeywordList
        fields = (
            'resource_uri', 'id'
        )


class FileSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='file-detail'
    )
    filename = serializers.CharField(read_only=True)

    def create(self, validated_data):
        file_object = super(FileSerializer, self).create(validated_data)
        if file_object.type == File.FILE_UNKNOWN:
            file_object.delete()
            raise FileTypeNotSupported(
                'Unsupported MIME type: %s' % file_object.mime
            )
        else:
            return file_object

    def validate(self, data):
        """
        Checks that the file is not too large and is unique within its batch.
        """
        content = data.get('content')
        if content is None:
            return data
        if content.size > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
            raise serializers.ValidationError(
                'File is too large! '
                'Expected at most %s, got %s.' % tuple(
                    map(filesizeformat,
                        [settings.DATA_UPLOAD_MAX_MEMORY_SIZE, content.size])
                )
            )
        batch = data['batch']
        if File.objects.filter(file_name=content.name, batch=batch).exists():
            raise serializers.ValidationError(
                'File is already uploaded to selected batch!'
            )
        return data

    class Meta:
        model = File
        fields = ('content', 'batch', 'created_at', 'need_ocr', 'filename',
                  'resource_uri', 'id')


class ProjectArchiveSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ProjectArchive
        fields = ('content_file', 'created_at')


class ProjectSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='project-detail'
    )
    batches = BatchUriSerializer(many=True, read_only=True)
    batch_count = serializers.CharField(
        source='batches.count', read_only=True)
    status_verbose = serializers.CharField(
        source='get_status_display', read_only=True)
    owner_username = serializers.CharField(
        source='owner.username', read_only=True)
    archive = ProjectArchiveSerializer(read_only=True)

    # TODO: replace to classifier.count when classifier model will be created
    classifier_count = serializers.CharField(
        source='batches.count', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['owner'] = user
        return super(ProjectSerializer, self).create(validated_data)


class BatchSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, required=False)
    filecount = serializers.IntegerField(
        source='files.count', read_only=True)
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), many=True, required=False
    )
    add_project = serializers.PrimaryKeyRelatedField(
        many=True, required=False, source='project',
        queryset=Project.objects.all()
    )
    remove_project = serializers.PrimaryKeyRelatedField(
        many=True, required=False, source='project',
        queryset=Project.objects.all()
    )

    name = serializers.CharField(required=True)
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='batch-detail'
    )
    owner_username = serializers.CharField(
        source='owner.username', read_only=True)
    create_date = serializers.CharField(
        source='upload_date', read_only=True)
    upload_date = serializers.CharField(
        source='get_upload_date', read_only=True)
    upload_time = serializers.CharField(
        source='get_upload_time', read_only=True)
    project_name = serializers.CharField(
        read_only=True
    )
    sentences_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Batch
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['owner'] = user
        return super(BatchSerializer, self).create(validated_data)
