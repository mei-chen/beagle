from rest_framework.routers import DefaultRouter

from viewsets import (
    RegExAPI, RegExApplyAPI, ReportAPI,
    SimModelListAPI, RecommendationAPI,
    KeywordAPI, KeywordListAPI, KeywordListSearchAPI)

analysis_router = DefaultRouter()
analysis_router.register('regex', RegExAPI, base_name='regex')
analysis_router.register('report', ReportAPI, base_name='report')
analysis_router.register('regex-apply', RegExApplyAPI, base_name='regex-apply')
analysis_router.register('simmodel', SimModelListAPI, base_name='simmodel')
analysis_router.register('recommend', RecommendationAPI, base_name='recommend')
analysis_router.register('keyword', KeywordAPI, base_name='keyword')
analysis_router.register('keywordlist', KeywordListAPI, base_name='keywordlist')
analysis_router.register(
    'keywordlist-search', KeywordListSearchAPI, base_name='keywordlist-search')
