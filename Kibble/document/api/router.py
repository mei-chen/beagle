from rest_framework.routers import DefaultRouter

from document.api.viewsets import (
    DocumentAPI, ConvertAPI, CleanupDocumentAPI, CleanupDocumentToolsAPI,
    SentenceAPI, PersonalDataAPI, CustomPersonalDataAPI
)

document_router = DefaultRouter()
document_router.register('document', DocumentAPI)
document_router.register('personal-data', PersonalDataAPI)
document_router.register('custom-personal-data', CustomPersonalDataAPI)
document_router.register('convertfile', ConvertAPI, basename='convertfile')
document_router.register(
    'cleanup-doc', CleanupDocumentAPI, basename='cleanup-doc')
document_router.register(
    'cleanup-doc-tool', CleanupDocumentToolsAPI, basename='cleanup-doc-tool')
document_router.register(
    'sentence-splitting', SentenceAPI, basename='sentence-splitting')
