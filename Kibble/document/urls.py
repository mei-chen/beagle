from django.conf.urls import url
from document import views


urlpatterns = [
    url(
        r'^batch-download/$',
        views.download_batch_documents,
        {'get_files_method': 'get_converted_documents'},
        name='batch_download'
    ),
    url(
        r'^batch-download-clean/$',
        views.download_batch_documents,
        {'get_files_method': 'get_cleaned_documents'},
        name='batch_download_clean'
    ),
    url(
        r'^download-sentences/$',
        views.download_document_sentences,
        name='download_sentences'
    )
]
