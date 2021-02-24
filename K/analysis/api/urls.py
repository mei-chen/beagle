from django.conf.urls import url, include

from analysis.api.router import analysis_router
from analysis.api.views import (
    RecommendSynonyms, PullSimilarSentences, AggregatedSentencesSearch
)

urlpatterns = [
    url(r'^v1/', include(analysis_router.urls)),

    url(r'^v1/recommend_synonyms/',
        RecommendSynonyms.as_view(),
        name='recommend_synonyms'),

    url(r'^v1/pull_similar_sentences/',
        PullSimilarSentences.as_view(),
        name='pull_similar_sentences'),

    url(r'^v1/aggregated_sentences_search/',
        AggregatedSentencesSearch.as_view(),
        name='aggregated_sentences_search')
]
