from django.conf.urls import patterns

from .document.endpoints import (
    DocumentListView,
    DocumentSortedListView,
    DocumentExportView,
    DocumentDetailView,
    DocumentViewedByView,
    ReanalysisActionView,
    ChangeOwnerActionView,
    FlagDocumentActionView,
    ChangePartiesActionView,
    UploadRawTextComputeView,
    DocumentUploadComputeView,
    DocumentPrepareExportView,
    DocumentAggregatedListView,
    IssueSentenceInvitesActionView,
    DocumentAnnotationsView
)

from .user.endpoints import (
    CurrentUserDetailView,
    CurrentUserProfileDetailView,
    CurrentUserCollaboratorsListView,
    UserDetailView,
    UserUnviewedDocsView,
    CurrentUserActiveSubscriptionDetailView,
    CurrentUserInitialSampleDocsView,
    UserAuthenticationView,
    CurrentUserSubscriptionsListView,
    OnlineLearnersListView,
    UserSettingsDetailView,
    UserRLTEFlagsDetailView,
    UserSpotExperimentsStatusView,
    UserSpotSuggestionsStatusView,
    UserAddSpotExperimentComputeView,
    UserRemoveSpotExperimentComputeView,
    UserResetSpotExperimentComputeView,
    UserActualCollaboratorsStatusView,
    UserProjectsListView,
)

from .ml.endpoints import (
    OnlineLearnerDetailView,
    OnlineLearnerSamplesDetailView,
    OnlineLearnerActiveView,
    OnlineLearnerResetView,
    OnlineLearnerTrainView
)

from .keyword.endpoints import (
    SearchKeywordDetailView,
    SearchKeywordActivateActionView,
    SearchKeywordDeactivateActionView,
    SearchKeywordListView,
)

from .clauses_statistics.endpoints import (
    ClausesStatisticDetailView,
    ClausesStatisticListView
)

from .invites.endpoints import (
    CurrentUserReceivedInvitationsListView,
    CurrentUserIssuedInvitationsListView,
    DocumentReceivedInvitationsListView,
    DocumentIssuedInvitationsListView
)

from .sentence.endpoints import (
    SentenceHistoryListView,
    SentenceAcceptActionView,
    SentenceDetailView,
    SentenceRejectActionView,
    SentenceLockDetailView,
    SentenceLikeActionView,
    SentenceDislikeActionView,
    SentenceUndoActionView,
    SentenceTagsView,
    SentenceSuggestedTagsView,
    SentenceBulkTagsView,
    SentenceCommentsListView,
)

from .inbox.endpoints import (
    InboxListView,
    InboxDetailView,
    InboxMarkAllView
)

from .status.endpoints import ApplicationStatusView

from .vw.endpoints import (
    VWLearnerPredictView,
    VWLearnerTrainView,
    VWLearnerInitView,
    VWLearnersListView,
    VWLearnerDetailView,
    VWLearnerResetView
)

from .internal.endpoints import (
    InternalUserDetailView,
    InternalDocumentUploadComputeView,
    InternalUserListView,
    InternalAddSubscriptionActionView,
    InternalNotifyUserView
)

from .statistics.endpoints import (
    StatisticsComputeView,
)

from .upload.endpoints import (
    ProcessEncryptedArchiveComputeView,
    SetDropboxTokenComputeView,
    SetGoogleDriveSecretStatusView,
    GetCloudAccessStatusView,
    AddCloudFolderComputeView,
    GetCloudFoldersListView,
    DeleteCloudFolderComputeView,
    RevokeGoogleDriveAccessView,
    RevokeDropboxAccessView,
)

from .batch.endpoints import (
    BatchDetailView,
    BatchReanalysisActionView,
    BatchCheckAnalysisStatusView,
    BatchPrepareExportView,
    BatchExportView,
    BatchExportSummaryView,
)


urlpatterns = patterns(
    '',
    ApplicationStatusView.to_url(),
    DocumentAggregatedListView.to_url(),
    DocumentListView.to_url(),
    DocumentSortedListView.to_url(),
    InternalDocumentUploadComputeView.to_url(),
    DocumentUploadComputeView.to_url(),
    DocumentDetailView.to_url(),
    DocumentViewedByView.to_url(),
    DocumentExportView.to_url(),
    DocumentPrepareExportView.to_url(),
    DocumentReceivedInvitationsListView.to_url(),
    DocumentIssuedInvitationsListView.to_url(),
    DocumentAnnotationsView.to_url(),
    InternalAddSubscriptionActionView.to_url(),
    InternalUserListView.to_url(),
    InternalUserDetailView.to_url(),
    InternalNotifyUserView.to_url(),
    IssueSentenceInvitesActionView.to_url(),
    FlagDocumentActionView.to_url(),
    ChangePartiesActionView.to_url(),
    ReanalysisActionView.to_url(),
    ChangeOwnerActionView.to_url(),
    CurrentUserDetailView.to_url(),
    CurrentUserProfileDetailView.to_url(),
    CurrentUserReceivedInvitationsListView.to_url(),
    CurrentUserIssuedInvitationsListView.to_url(),
    CurrentUserCollaboratorsListView.to_url(),
    CurrentUserSubscriptionsListView.to_url(),
    CurrentUserActiveSubscriptionDetailView.to_url(),
    CurrentUserInitialSampleDocsView.to_url(),
    OnlineLearnersListView.to_url(),
    UserSettingsDetailView.to_url(),
    UserRLTEFlagsDetailView.to_url(),
    UserAuthenticationView.to_url(),
    UserDetailView.to_url(),
    UserUnviewedDocsView.to_url(),
    UserSpotExperimentsStatusView.to_url(),
    UserSpotSuggestionsStatusView.to_url(),
    UserAddSpotExperimentComputeView.to_url(),
    UserRemoveSpotExperimentComputeView.to_url(),
    UserResetSpotExperimentComputeView.to_url(),
    UserActualCollaboratorsStatusView.to_url(),
    UserProjectsListView.to_url(),
    SentenceDetailView.to_url(),
    SentenceHistoryListView.to_url(),
    SentenceAcceptActionView.to_url(),
    SentenceRejectActionView.to_url(),
    SentenceUndoActionView.to_url(),
    SentenceLockDetailView.to_url(),
    SentenceLikeActionView.to_url(),
    SentenceDislikeActionView.to_url(),
    SentenceBulkTagsView.to_url(),
    SentenceTagsView.to_url(),
    SentenceSuggestedTagsView.to_url(),
    SentenceCommentsListView.to_url(),
    UploadRawTextComputeView.to_url(),
    InboxDetailView.to_url(),
    InboxMarkAllView.to_url(),
    InboxListView.to_url(),
    OnlineLearnerSamplesDetailView.to_url(),
    OnlineLearnerActiveView.to_url(),
    OnlineLearnerResetView.to_url(),
    OnlineLearnerTrainView.to_url(),
    OnlineLearnerDetailView.to_url(),
    SearchKeywordActivateActionView.to_url(),
    SearchKeywordDeactivateActionView.to_url(),
    SearchKeywordDetailView.to_url(),
    SearchKeywordListView.to_url(),
    ClausesStatisticDetailView.to_url(),
    ClausesStatisticListView.to_url(),
    VWLearnerPredictView.to_url(),
    VWLearnerTrainView.to_url(),
    VWLearnerInitView.to_url(),
    VWLearnersListView.to_url(),
    VWLearnerDetailView.to_url(),
    VWLearnerResetView.to_url(),
    StatisticsComputeView.to_url(),
    ProcessEncryptedArchiveComputeView.to_url(),
    GetCloudAccessStatusView.to_url(),
    SetDropboxTokenComputeView.to_url(),
    SetGoogleDriveSecretStatusView.to_url(),
    AddCloudFolderComputeView.to_url(),
    GetCloudFoldersListView.to_url(),
    DeleteCloudFolderComputeView.to_url(),
    RevokeGoogleDriveAccessView.to_url(),
    RevokeDropboxAccessView.to_url(),
    BatchDetailView.to_url(),
    BatchReanalysisActionView.to_url(),
    BatchCheckAnalysisStatusView.to_url(),
    BatchPrepareExportView.to_url(),
    BatchExportView.to_url(),
    BatchExportSummaryView.to_url(),
)
