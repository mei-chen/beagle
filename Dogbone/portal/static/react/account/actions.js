var Reflux = require('reflux');


var PaginatedActions = [
  'setFilterQuery',
  'requestPrevPage',
  'requestNextPage',
  'requestSpecificPage'
];


var ProjectActions = Reflux.createActions([
  'changeOwner',
  'inviteUser',
  'uninviteUser',
  'deleteDocument',
  'refresh',
].concat(PaginatedActions));


var InvitedProjectActions = Reflux.createActions([
  'refresh',
].concat(PaginatedActions));


var AccountActions = Reflux.createActions([
]);


var LearnersActions = Reflux.createActions([
  'resetLearner',
  'deleteLearner',
  'activateLearner',
  'deactivateLearner',
]);


var KeywordsActions = Reflux.createActions([
  'addKeyword',
  'deleteKeyword',
  'activateKeyword',
  'deactivateKeyword',
]);


var SettingsActions = Reflux.createActions([
  'changeFinishProcesEmailNotif',
  'changeColabInvEmailNotif',
  'changeCommentMentionEmailNotif',
  'changeOwnChangeEmailNotif',
  'changeAllNotifications',
  'changeEmailDigest',
  'changeDefaultRepView',
  'changeLearnerHelpText'
]);


module.exports = {
  ProjectActions,
  InvitedProjectActions,
  AccountActions,
  LearnersActions,
  KeywordsActions,
  SettingsActions
};
