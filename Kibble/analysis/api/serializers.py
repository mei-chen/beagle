from rest_framework import serializers

from analysis.models import RegEx, Report, Keyword, KeywordList, SimModel
from portal.models import Batch


class RegExSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='regex-detail'
    )

    class Meta:
        model = RegEx
        fields = '__all__'


class RegExApplySerializer(serializers.Serializer):
    regex = serializers.PrimaryKeyRelatedField(queryset=RegEx.objects.all())
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

    class Meta:
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='report-detail'
    )

    class Meta:
        model = Report
        fields = '__all__'


class SimModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimModel
        fields = '__all__'


class RecommendationSerializer(serializers.Serializer):
    word = serializers.CharField()
    model = serializers.CharField()

    def validate_model(self, value):
        if not SimModel.objects.filter(api_name=value).exists():
            raise serializers.ValidationError(
                "No such simmodel {}".format(value))
        return value

    class Meta:
        fields = '__all__'


class KeywordSerializer(serializers.ModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='keyword-detail'
    )

    class Meta:
        model = Keyword
        fields = '__all__'


class KeywordListSerializer(serializers.ModelSerializer):
    keywords = KeywordSerializer(many=True, required=False)
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='keywordlist-detail'
    )

    def __create_keywords(self, instance, keywords=[]):
        for item in keywords:
            Keyword.objects.create(
                keyword_list=instance, content=item['content'])

    def create(self, validated_data):

        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        
        instance = KeywordList(name=validated_data['name'], origin=validated_data['origin'], owner=user)
        instance.save()

        self.__create_keywords(instance, validated_data.get('keywords', []))

        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data['name']
        instance.save()

        keywords = validated_data.get('keywords', [])
        to_keep = list(filter(lambda x: x.get('uuid'), keywords))
        to_create = list(filter(lambda x: not x.get('uuid', False), keywords))

        instance.keywords.exclude(uuid__in=[x.get('uuid') for x in to_keep]).delete()
        if to_create:
            self.__create_keywords(instance, to_create)

        return instance

    class Meta:
        model = KeywordList
        fields = '__all__'


class KeywordListSearchySerializer(serializers.Serializer):
    keywordlist = serializers.PrimaryKeyRelatedField(
        queryset=KeywordList.objects.all())
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())
    obfuscate = serializers.BooleanField()

    class Meta:
        fields = '__all__'
