# Third Party
from rest_framework import serializers

# App
from reports.models import Report, ReportShared, LicenseStatistic


class ReportSharedSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()

    @staticmethod
    def get_share_url(obj):
        return obj.share_url()

    class Meta:
        model = ReportShared
        fields = (
            'id', 'token', 'report', 'user', 'created_at',
            'share_url', 'name'
        )


class ReportSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    @staticmethod
    def get_content(obj):
        is_private = not obj.public_repo
        content = obj.content_for_frontend
        content['is_private'] = is_private

        return content

    class Meta:
        model = Report
        fields = (
            'uuid', 'content'
        )


class ReportListSerializer(serializers.ModelSerializer):
    report_shared = ReportSharedSerializer(read_only=True, many=True)
    overall_risk = serializers.SerializerMethodField()
    license_length = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_private = serializers.SerializerMethodField()

    @staticmethod
    def get_overall_risk(obj):
        return obj.content_for_frontend.get('overall_risk')

    @staticmethod
    def get_status(obj):
        return obj.content_for_frontend.get('status')

    @staticmethod
    def get_license_length(obj):
        if 'licenses' in obj.content:
            return len(obj.content['licenses'])
        else:
            return None

    @staticmethod
    def get_is_private(obj):
        return not obj.public_repo

    class Meta:
        model = Report
        fields = (
            'id', 'uuid', 'created_at', 'url', 'status', 'report_shared',
            'overall_risk', 'license_length', 'is_private'
        )


class LicenseStatisticSerializer(serializers.ModelSerializer):
    risks = serializers.SerializerMethodField()

    def get_risks(self, obj):
        return obj.get_risks()

    class Meta:
        model = LicenseStatistic
        fields = (
            'name', 'risks'
        )
