from rest_framework.routers import DefaultRouter

from analysis.api.viewsets import (
    RegExAPI, RegExApplyAPI, ReportAPI,
    SimModelListAPI, RecommendationAPI,
    KeywordAPI, KeywordListAPI, KeywordListSearchAPI)

analysis_router = DefaultRouter()
analysis_router.register('regex', RegExAPI, basename='regex')
analysis_router.register('report', ReportAPI, basename='report')
analysis_router.register('regex-apply', RegExApplyAPI, basename='regex-apply')
analysis_router.register('simmodel', SimModelListAPI, basename='simmodel')
analysis_router.register('recommend', RecommendationAPI, basename='recommend')
analysis_router.register('keyword', KeywordAPI, basename='keyword')
analysis_router.register('keywordlist', KeywordListAPI, basename='keywordlist')
analysis_router.register(
    'keywordlist-search', KeywordListSearchAPI, basename='keywordlist-search')
