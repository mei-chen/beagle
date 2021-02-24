from os.path import basename

from rest_framework import serializers

from watcher.models import CloudFolder


class CloudFolderSerializer(serializers.ModelSerializer):

    class Meta:
        model = CloudFolder
        exclude = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Unlike Google Drive, Dropbox supports and returns absolute paths,
        # so unify things here a bit by simply using folder's names
        validated_data['folder_path'] = basename(validated_data['folder_path'])
        return super(CloudFolderSerializer, self).create(validated_data)
