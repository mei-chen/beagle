/**
 * ReportActions
 *
 * Actions available to the report page
 *
 */
var Reflux = require('reflux');

var ReportActions = Reflux.createActions({
  acceptChange: { asyncResult: true }, // converse is `rejectChange`
  addAnnotation: { asyncResult: true },
  addComment: { asyncResult: true },
  submitComment: { asyncResult: true },
  deleteComment: { asyncResult: true },
  addSentence: { asyncResult: true },
  deleteAnnotation: { asyncResult: true },
  deleteSentence: { asyncResult: true },
  editAnnotation: { asyncResult: true },
  editText: { asyncResult: true },
  changeOwner: { asyncResult: true },
  inviteUser: { asyncResult: true },
  uninviteUser: { asyncResult: true },
  likeSentence: { asyncResult: true },
  dislikeSentence: { asyncResult: true },
  clearUserLike: { asyncResult: true },
  clearUserDislike: { asyncResult: true },
  addBulkTags: { asyncResult: true },
  deleteBulkTags: { asyncResult: true },
  approveBulkTags: { asyncResult: true},
  addTag: { asyncResult: true },
  deleteTag: { asyncResult: true },
  approveSuggestedTag: { asyncResult: true },
  rejectSuggestedTag: { asyncResult: true },
  getCommentPage: { asyncResult: true },
  assignSentences: { asyncResult: true },
  refreshAnalysis: { asyncResult: true },
  rejectChange: { asyncResult: true },
  saveSentence: { asyncResult: true }
});


module.exports = ReportActions;
