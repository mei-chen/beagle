import axios from 'axios';
import { Map, List } from 'immutable';
import _ from 'lodash';

// App
import intersectionArrayOfObjects from 'utils/intersectionArrayOfObjects';
import log from 'utils/logging';
import { MODULE_NAME } from 'common/utils/constants';
import { Notification } from 'common/redux/modules/transientnotification';

// Current Doc
const node = document.getElementById('_uuid');
const docUUID = node != null ? node.value : null;

// CONSTANTS
const BASE_URL = '/api/v1/document/';
const CURRENT_NAME = 'report';
// const MAX_RETRIES = 3;

// ACTION CONSTANTS
// Sync
const CHANGE_OWNER_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CHANGE_OWNER_SUCCESS`;
const ADD_COLLABORATOR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_COLLABORATOR`;
const REMOVE_COLLABORATOR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/REMOVE_COLLABORATOR`;

const RESET_REQUEST_RETRIES = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET_REQUEST_RETRIES`;
const RESET_RELEASE_RETRIES = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET_RELEASE_RETRIES`;

const FINISHED_REQUESTING = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/FINISHED_REQUESTING`;
const FINISHED_RELEASING = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/FINISHED_RELEASING`;

const SET_LOCK = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SET_LOCK`;
const UN_SET_LOCK = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/REMOVE_LOCK`;

const ADD_COMMENT = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_COMMENT`;
const DELETE_COMMENT_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_COMMENT_REQUEST`;
const DELETE_COMMENT_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_COMMENT_SUCCESS`;

// Async
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

const CREATE_LOCK_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CREATE_LOCK_REQUEST`;
const CREATE_LOCK_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CREATE_LOCK_SUCCESS`;

const RELEASE_LOCK_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RELEASE_LOCK_REQUEST`;
const RELEASE_LOCK_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RELEASE_LOCK_SUCCESS`;

const SUBMIT_SENTENCE_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SUBMIT_SENTENCE_SUCCESS`;

const LIKE_SENTENCE_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/LIKE_SENTENCE_REQUEST`;
const CLEAR_LIKE_SENTENCE_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CLEAR_LIKE_SENTENCE_REQUEST`;

const DISLIKE_SENTENCE_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DISLIKE_SENTENCE_REQUEST`;
const CLEAR_DISLIKE_SENTENCE_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CLEAR_DISLIKE_SENTENCE_REQUEST`;

const ADD_TAG_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_TAG_REQUEST`;
const DELETE_TAG_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_TAG_REQUEST`;

const ADD_BULK_TAG_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_BULK_TAG_REQUEST`;
const DELETE_BULK_TAG_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_BULK_TAG_REQUEST`;

const APPROVE_SUGGESTED_TAG_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/APPROVE_SUGGESTED_TAG_REQUEST`;
const APPROVE_BULK_TAG_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/APPROVE_BULK_TAG_REQUEST`;

const ASSIGN_SENTENCES_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ASSIGN_SENTENCES_REQUEST`;

const SUBMIT_EDIT_SENTENCE_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SUBMIT_EDIT_SENTENCE_REQUEST`;
const SUBMIT_EDIT_SENTENCE_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SUBMIT_EDIT_SENTENCE_SUCCESS`;

const LOCK_CHANGED_SOCKET = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/LOCK_CHANGED_SOCKET`;

const PREPARE_DOCUMENT_EXPORT_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/PREPARE_DOCUMENT_EXPORT_REQUEST`;

// Front end
const DOCUMENT_REANALYZE = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DOCUMENT_REANALYZE`;
const TOGGLE_DISPLAY_COMPONENT_BOOLEAN = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/TOGGLE_DISPLAY_COMPONENT_BOOLEAN`;
const UPDATE_SELECTED_SENTENCES = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/UPDATE_SELECTED_SENTENCES`;

// Socket
const DOCUMENT_SENTENCE_CHANGED_SOCKET = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DOCUMENT_SENTENCE_CHANGED_SOCKET`;
const DOCUMENT_WHOLE_CHANGED_SOCKET = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DOCUMENT_WHOLE_CHANGED_SOCKET`;
const DOCUMENT_BULK_TAGS_RESPONSE = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DOCUMENT_BULK_TAGS_RESPONSE`;

const GET_LEARNERS_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_LEARNERS_SUCCESS`;

// Helpers
const _getDocumentURL = () => `${BASE_URL}${docUUID}`;
const _getSentenceURL = (sentenceIdx) => `${_getDocumentURL()}/sentence/${sentenceIdx}`;
const _getSentenceLockURL = (sentenceIdx) => `${_getSentenceURL(sentenceIdx)}/lock`;
const _getDocumentSentenceTagURL = () => `${_getDocumentURL()}/sentence/tags`;
/*
* lightwieght compare function to use in the intersectionArrayOfObjects
* function. Used to find common tags in the bulk tag tools.
*/
const _compareObjects = (a,b) => {
  //first check to see if the attributes exist
  if (a.label && b.label && a.approved !== undefined && b.approved !== undefined) {
    return a.label === b.label;
  }
  return false;
};

const _getCommonAnnotations = (sentences) => {
  const sentenceAnnotations = sentences.map(s => {
    return s.annotations || [];
  });

  // initialize common annotations as first sentence annotations list
  let commonAnnotations = sentenceAnnotations[0];
  // for the rest of the sentence tags... `slice(1)`
  sentenceAnnotations.slice(1).forEach(currentSentenceAnnotationsList => {
    // repeatedly take intersection of each tags list
    commonAnnotations = intersectionArrayOfObjects(commonAnnotations, currentSentenceAnnotationsList, _compareObjects);
  });

  return _.chain(commonAnnotations)
      .map(a => {
        return {
          name: a.label.toLowerCase(),
          label: a.label.toLowerCase(),
          perm: false,
          class: a.type,
          suggested: (!a.approved && a.type === window.SUGGESTED_TAG_TYPE),
          key: `${a.label.toLowerCase()}-${a.type}-${a.user}`
        };
      })
      .sortBy('label')
      .value();
};

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = (data) => {
  return {
    type: GET_SUCCESS,
    data
  }
};

const changeOwnerSuccess = (user) => {
  return {
    type: CHANGE_OWNER_SUCCESS,
    user
  }
}

const addCollaborator = (user) => {
  return {
    type: ADD_COLLABORATOR,
    user
  }
}

export const removeCollaborator = (user) => {
  return {
    type: REMOVE_COLLABORATOR,
    user
  }
}

const submitSentenceSuccess = (id, text) => {
  return {
    type: SUBMIT_SENTENCE_SUCCESS,
    id,
    text
  }
}

// Lock actions
const createLockRequest = (idx) => {
  return {
    type: CREATE_LOCK_REQUEST,
    idx
  }
}

export const createLockSuccess = (data) => {
  return {
    type: CREATE_LOCK_SUCCESS,
    data
  }
}

const releaseLockRequest = (idx) => {
  return {
    type: RELEASE_LOCK_REQUEST,
    idx
  }
}

export const lockChangedSocket = (data) => {
  return {
    type: LOCK_CHANGED_SOCKET,
    data
  }
}

const releaseLockSuccess = (data) => {
  return {
    type: RELEASE_LOCK_SUCCESS,
    data
  }
}

const finishedReleasing = (idx) => {
  return {
    type: FINISHED_RELEASING,
    idx
  }
}

const finishedRequesting = (idx) => {
  return {
    type: FINISHED_REQUESTING,
    idx
  }
}

const likeSentenceRequest = () => {
  return {
    type: LIKE_SENTENCE_REQUEST
  }
}

const dislikeSentenceRequest = () => {
  return {
    type: DISLIKE_SENTENCE_REQUEST
  }
}

const clearLikeSentenceRequest = () => {
  return {
    type: CLEAR_LIKE_SENTENCE_REQUEST
  }
}

const clearDislikeSentenceRequest = () => {
  return {
    type: CLEAR_DISLIKE_SENTENCE_REQUEST
  }
}

const addTagRequest = () => {
  return {
    type: ADD_TAG_REQUEST
  }
}

const deleteTagRequest = () => {
  return {
    type: DELETE_TAG_REQUEST
  }
}

const approveSuggestedTagRequest = () => {
  return {
    type: APPROVE_SUGGESTED_TAG_REQUEST
  }
}

const assignSentencesRequest = () => {
  return {
    type: ASSIGN_SENTENCES_REQUEST
  }
}

const deleteBulkTagsRequest = (annotations) => {
  return {
    type: DELETE_BULK_TAG_REQUEST,
    annotations
  }
}

const addBulkTagsRequest = (annotations) => {
  return {
    type: ADD_BULK_TAG_REQUEST,
    annotations
  }
}

const approveBulkTagsRequest = () => {
  return {
    type: APPROVE_BULK_TAG_REQUEST
  }
}

export const documentSentenceChangedSocket = (data) => {
  return {
    type: DOCUMENT_SENTENCE_CHANGED_SOCKET,
    data
  }
}

export const documentSentenceTagsResponse = (sentences) => {
  return {
    type: DOCUMENT_BULK_TAGS_RESPONSE,
    sentences
  }
}

export const documentWholeChangedSocket = (data) => {
  return {
    type: DOCUMENT_WHOLE_CHANGED_SOCKET,
    data
  }
}

export const setLock = (idx) => {
  return {
    type: SET_LOCK,
    idx
  }
}

export const unSetLock = (idx) => {
  return {
    type: UN_SET_LOCK,
    idx
  }
}

export const addComment = (idx, comment) => {
  return {
    type: ADD_COMMENT,
    idx,
    comment
  }
}

const deleteCommentRequest = () => {
  return {
    type: DELETE_COMMENT_REQUEST
  }
}

const deleteCommentSuccess = (idx, uuid) => {
  return {
    type: DELETE_COMMENT_SUCCESS,
    idx,
    uuid
  }
}

export const submitEditSentenceRequest = (data) => {
  return {
    type: SUBMIT_EDIT_SENTENCE_REQUEST,
    data
  }
}

export const submitEditSentenceSuccess = (idx, sentence) => {
  return {
    type: SUBMIT_EDIT_SENTENCE_SUCCESS,
    idx,
    sentence
  }
}

export const prepareDocumentExportRequest = (data) => {
  return {
    type: PREPARE_DOCUMENT_EXPORT_REQUEST,
    data
  }
}

export const reAnalyzeDocument = () => {
  return {
    type: DOCUMENT_REANALYZE,
  }
}

// Toggles between true or false on states that manage front
export const toggleDisplayComponentBoolean = (key, value) => {
  return {
    type: TOGGLE_DISPLAY_COMPONENT_BOOLEAN,
    key,
    value
  }
}

export const updateSelectedSentences = (selectedSentences) => {
  return {
    type: UPDATE_SELECTED_SENTENCES,
    selectedSentences
  }
}

export const getLearnersSuccess = (learners) => {
  return {
    type: GET_LEARNERS_SUCCESS,
    learners
  }
}

// Async actions
export const getFromServer = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get(_getDocumentURL())
      .then(response => {
        dispatch(getSuccess(response.data))
        dispatch(getLearners())
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const changeOwner = (user) => {
  Intercom('trackUserEvent', 'change-owner');
  return (dispatch) => {
    return axios.post(`${_getDocumentURL()}/owner`, { owner: user.email })
      .then(() => {
        dispatch(changeOwnerSuccess(user));
        dispatch(getFromServer());
      }).catch((err) => {
        log.error(err.response || err);
        dispatch(Notification.error(`Changing owner ${user.email} failed`));
      })
  }
};

export const inviteUser = (invitee, sentenceIdx) => {
  Intercom('trackUserEvent', 'invite-collaborator');
  return (dispatch) => {
    const _url = `${_getDocumentURL()}/issued_invitations?external=True`;
    return axios.post(_url, { invitee, sentenceIdx })
      .then(response => {
        dispatch(addCollaborator(response.data.objects[0].invitee));
        dispatch(Notification.success(`${invitee} was invited to collaborate.`));
      }).catch((err) => {
        log.error(err.response || err);
        dispatch(Notification.error(`Invite to ${invitee} failed.`));
      })
  }
}

export const unInviteUser = (user) => {
  Intercom('trackUserEvent', 'uninvite-collaborator');
  return (dispatch) => {
    const url = `${_getDocumentURL()}/issued_invitations?external=True`;
    return axios({
      method: 'delete',
      url,
      data: { email: user.email }
    }).then(() => {
      dispatch(removeCollaborator(user));
    }).catch((err) => {
      log.error(err.response || err);
      dispatch(Notification.error(`${user.email} was not successfully removed from the document.`));
    })
  }
}

export const requestLock = (idx) => {
  return (dispatch, getState) => {
    const state = getState();
    const sentence = state.report.get('analysis').get('sentences').find(x => x.get('idx') === idx).toJS();

    if (sentence.lock) {
      log.info('report: tried to request lock that already exists');
      return;
    } else if (sentence.isRequesting) {
      log.info('report: already trying to request lock', idx);
      return;
    } else if (sentence.isReleasing) {
      log.info('report: trying to request lock that is pending release');
      return;
    }

    dispatch(createLockRequest(idx));
    return axios.put(_getSentenceLockURL(idx))
      .then(response => {
        const { success, sentence } = response.data;
        if (!success) return;

        dispatch(createLockSuccess({ idx, sentence }));
      }).catch((err) => {
        dispatch(finishedRequesting(idx));
        log.error(err, err.response && err.response.data && err.response.data.error)
      })
  }
}

export const releaseLock = (idx) => {
  return (dispatch, getState) => {
    const state = getState();
    const sentence = state.report.get('analysis').get('sentences').find(x => x.get('idx') === idx).toJS();

    if (!sentence.lock) {
      log.info('report: tried to release lock that is not held');
      return;
    } else if (sentence.isRequesting) {
      log.info('report: trying to release lock that is pending REQUEST');
      return;
    } else if (sentence.isReleasing) {
      log.info('report: trying to release lock that is pending release');
      return;
    }

    dispatch(releaseLockRequest(idx));
    return axios.delete(_getSentenceLockURL(idx))
      .then(response => {
        const { success, sentence } = response.data;
        if (!success) return;
        dispatch(releaseLockSuccess({ idx, sentence }));
      }).catch((err) => {
        dispatch(finishedReleasing(idx));
        log.error(err.response || err)
      })
  }
}

export const releaseLockOnDisconnect = () => {
  return (dispatch, getState) => {
    const state = getState();
    const sentence = state.report.get('analysis').get('sentences').find(x => x.get('lock') !== null);

    if (!sentence) return false;
    dispatch(releaseLock(sentence.get('idx')));
  }
}

export const submitComment = (idx, comment) => {
  return (dispatch) => {
    return axios.post(`${_getSentenceURL(idx)}/comments`, { message: comment })
      .then(() => {
        dispatch(submitSentenceSuccess());
      }).catch(err => {
        if (err.response.data.message.includes('TooManyCommentsException')) {
          dispatch(Notification.error("You can't add more comments in this Sentence"));
        }
        log.error(err.response || err)
      })
  }
}

export const getComments = (idx, page) => {
  return (dispatch) => {
    return axios.get(`${_getSentenceURL(idx)}/comments?page=${page}`)
      .then(resp => {
        resp.data.objects.forEach(comment => dispatch(addComment(idx, comment)));
        return resp;
      }).catch(err => {
        log.error(err.response || err)
      })
  }
}

export const deleteCommentOnServer = (idx, uuid) => {
  return dispatch => {
    dispatch(deleteCommentRequest());
    return axios({
      method: 'DELETE',
      url: `${_getSentenceURL(idx)}/comments/`,
      data: { comment_uuid: uuid }
    })
      .then(() => {
        dispatch(deleteCommentSuccess(idx, uuid))
      }).catch(err => {
        log.error(err.response || err)
      })
  }
}

export const submitEditSentence = (idx, data) => {
  return (dispatch) => {
    dispatch(submitEditSentenceRequest());
    return axios.put(_getSentenceURL(idx), data)
      .then(resp => dispatch(submitEditSentenceSuccess(idx, resp.data)))
      .catch(err=> {
        log.error(err.response || err);
      })
  }
}

export const acceptChange = (idx) => {
  Intercom('trackUserEvent', 'accept-sentence-changes');

  return (dispatch) => {
    return axios.post(`${_getSentenceURL(idx)}/accept`)
      .catch(err => {
        log.error('accept failed', err.response || err)
        dispatch(Notification.error('Failed accepting the changes'));
      })
  }
}

export const rejectChange = (idx) => {
  Intercom('trackUserEvent', 'reject-sentence-changes');

  return (dispatch) => {
    return axios.post(`${_getSentenceURL(idx)}/reject`)
      .catch(err => {
        log.error('reject failed', err.response || err)
        dispatch(Notification.error('Failed rejecting the changes'));
      })
  }
}

export const addBulkTags = (sentenceIdxs, annotations) => {
  Intercom('trackUserEvent', 'add-sentences-bulk-tag');

  const dataContents = sentenceIdxs.map(sentenceIdx => {
    return { sentenceIdx, annotations }
  });
  const data = { sentences : dataContents }

  return (dispatch) => {
    dispatch(addBulkTagsRequest(annotations));
    return axios.post(_getDocumentSentenceTagURL(), data)
      .catch(err => {
        log.error('add annotations ' + annotations.map(a => a.label) + ' failed', err.response || err);
      })
  }
}

export const approveBulkTags = (sentenceIdxs, annotations) => {
  Intercom('trackUserEvent', 'approve-sentences-bulk-tag');

  const dataContents = sentenceIdxs.map(sentenceIdx => {
    return { sentenceIdx, annotations }
  });
  const data = { sentences : dataContents }
  return (dispatch) => {
    dispatch(approveBulkTagsRequest());
    return axios.put(_getDocumentSentenceTagURL(), data)
      .catch(err => {
        log.error('approve suggested tags [' + annotations.map(a => a.label) + '] failed', err.response || err);
      })
  }
}

export const deleteBulkTags = (sentenceIdxs, annotations) => {
  Intercom('trackUserEvent', 'delete-sentences-bulk-tag');

  const dataContents = sentenceIdxs.map(sentenceIdx => {
    return { sentenceIdx, annotations }
  });
  const data = { sentences : dataContents };
  const url = _getDocumentSentenceTagURL();
  return (dispatch) => {
    dispatch(deleteBulkTagsRequest(annotations));
    return axios({ method: 'delete', url, data })
      .catch(err => log.error('delete tags ' + annotations.map(a => a.label) + ' failed', err.response || err));
  }
}

export const likeSentence = (idx) => {
  Intercom('trackUserEvent', 'like-sentence');

  return (dispatch) => {
    dispatch(likeSentenceRequest());

    return axios.post(`${_getSentenceURL(idx)}/like`)
      .catch(err => log.error('like failed', err.response || err));
  }
}

export const dislikeSentence = (idx) => {
  Intercom('trackUserEvent', 'dislike-sentence');

  return (dispatch) => {
    dispatch(dislikeSentenceRequest());

    return axios.post(`${_getSentenceURL(idx)}/dislike`)
        .catch(err => log.error('dislike failed', err.response || err));
  }
}

export const clearLikeSentence = (idx) => {
  Intercom('trackUserEvent', 'clear-sentence-like');

  return (dispatch) => {
    dispatch(clearLikeSentenceRequest());

    return axios.delete(`${_getSentenceURL(idx)}/like`)
        .catch(err => log.error('clear like failed', err.response || err));
  }
}

export const clearDislikeSentence = (idx) => {
  Intercom('trackUserEvent', 'clear-sentence-dislike');

  return (dispatch) => {
    dispatch(clearDislikeSentenceRequest());

    return axios.delete(`${_getSentenceURL(idx)}/dislike`)
      .catch(err => log.error('clear dislike failed', err.response || err));
  }
}

export const addTag = (idx, tag) => {
  Intercom('trackUserEvent', 'add-sentence-tag');

  return (dispatch) => {
    dispatch(addTagRequest());

    return axios.post(`${_getSentenceURL(idx)}/tags`, { tag })
        .catch(err => log.error('dislike failed', err.response || err));
  }
}

export const deleteTag = (idx, annotation) => {
  Intercom('trackUserEvent', 'delete-sentence-tag');

  const { sublabel, party, type, label } = annotation;
  return (dispatch) => {
    dispatch(deleteTagRequest());

    const data = { tag: label, sublabel, party, type };
    const url = `${_getSentenceURL(idx)}/tags`;

    return axios({ method: 'delete', url, data })
      .catch(err => log.error('delete tag ' + label + ' failed', err.response || err));
  }
}

export const approveSuggestedTag = (idx, annotation) => {
  Intercom('trackEvent', 'approve-suggested-tag');

  return (dispatch) => {
    dispatch(approveSuggestedTagRequest());

    const { label } = annotation;

    return axios.put(`${_getSentenceURL(idx)}/sugg_tags`, { tag: label })
        .catch(resp => log.error(`approve suggested tag "${label}" failed`, resp));
  }
}

export const assignSentences = (email, sentences) => {
  return (dispatch) => {
    dispatch(assignSentencesRequest());

    return axios.post(`${_getDocumentURL()}/sentence/assign`, { email, sentences })
      .then(() => {
        dispatch(Notification.success(`Assigned ${sentences.length} clauses to user ${email} successfully`));
      }).catch(err => {
        log.error('uninvite failed: ', err.response || err);
        dispatch(Notification.error(`Assigning clauses to user ${email} failed`));
      });
  }
}

export const prepareDocumentExport = (data = {}) => {
  return (dispatch) => {
    dispatch(prepareDocumentExportRequest(data));
    return axios.post(`${_getDocumentURL()}/prepare_export`, data)
        .catch(resp => log.error('Documet prepare export failed', resp));
  }
}

export const reAnalyze = (you, them) => {
  return (dispatch) => {
    dispatch(reAnalyzeDocument());
    return axios.post(`${_getDocumentURL()}/parties` , JSON.stringify({
      parties: [
        you,
        them
      ]
    })).then(() => {
      dispatch(getFromServer());
    }).catch(resp => log.error('Documet re-analyze failed', resp));
  }
}

export const getLearners = () => {
  return (dispatch) => {
    return axios.get('/api/v1/user/me/learners')
      .then(response => {
        dispatch(getLearnersSuccess(response.data.objects));
      }).catch(err => {
        log.error(err.response || err);
      });
  }
}

// REDUCERS
const initialState = Map({
  // Database Sentence
  agreement_type: null,
  agreement_type_confidence: null,
  analysis: Map({
    parties: Map({
      you: Map({}),
      them: Map({})
    }),
    sentences: List(),
  }),
  collaborators: List(),
  created: null,
  failed: null,
  is_initsample: null,
  keywords_state: List(),
  learners_state: List(),
  original_name: null,
  owner: Map({}),
  processing_begin_timestamp: null,
  processing_end_timestamp: null,
  report_url: null,
  status: null,
  title: null,
  url: null,
  uuid: null,
  learners: List(),

  // Front end state
  isInitialized: false,
  areLearnersInitialized: false,
  isFetching: false,
  isBulkTagRequesting: false,
  showUnconfidentPopover : false,
  exportState: {
    isClicked: false,
    showPopover: false,
    isLoading: false,
    isReady: false,
    hasExportIcon: true
  },
  bulkAnnotations: List(),
  selectedSentences: List()
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state.merge({
      isFetching: false
    });
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      isFetching: false,
      ... action.data
    });
  }

  case CHANGE_OWNER_SUCCESS: {
    return state;
  }

  case ADD_COLLABORATOR: {
    return state.merge({
      collaborators: state.get('collaborators').push(Map(action.user))
    });
  }

  case REMOVE_COLLABORATOR: {
    return state.update('collaborators', collaborators => collaborators.filter(x => x.get('username') !== action.user.username));
  }

  case SUBMIT_SENTENCE_SUCCESS: {
    // No need to update the state as it's saved from the socket
    return state;
  }

  case CREATE_LOCK_REQUEST: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.idx),
        x => x.merge({
          isRequesting: true,
          requestRetries: (x.requestRetries || 0) + 1
        })  // Merging the given sentence
      )
    )
  }

  case CREATE_LOCK_SUCCESS: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.data.idx),
        x => x.merge({
          ... action.data.sentence,
          isReleasing: false,
          isRequesting: false,
          requestRetries: 0
        })  // Merging the given sentence
      )
    )
  }

  case RELEASE_LOCK_REQUEST: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.idx),
        x => x.merge({
          isRequesting: true,
          isReleasing: true,
          releaseRetries: (x.get('releaseRetries') || 0) + 1
        })  // Merging the given sentence
      )
    )
  }

  case RELEASE_LOCK_SUCCESS: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.data.idx),
        x => x.merge({
          lock: action.data.sentence.lock,
          isRequesting: false,
          isReleasing: false,
          releaseRetries: 0
        })  // Merging the given sentence
      )
    )
  }

  case LOCK_CHANGED_SOCKET: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.data.idx),
        x => x.merge({
          lock: action.data.sentence.lock,
          isRequesting: false,
          isReleasing: false,
          releaseRetries: 0
        })  // Merging the given sentence
      )
    )
  }

  case RESET_REQUEST_RETRIES: {
    return state.set('requestRetries', 0);
  }

  case RESET_RELEASE_RETRIES: {
    return state.set('releaseRetries', 0);
  }

  case DOCUMENT_SENTENCE_CHANGED_SOCKET: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.data.idx),
        x => {
          if (!x.get('lock') && action.data.sentence.lock) {
            // Only merge lock and nothing else, as leads to bugs
            return x.merge({ lock: action.data.sentence.lock })
          } else { // update everythin as assume
            return x.merge(action.data.sentence) // Merging the given sentence
              .merge({ // Merge latest revision if keys exist else make key undefined
                latestRevision: action.data.sentence.latestRevision || undefined
              })
          }
        }
      ) // End of Update
    ); // End of updateIn
  }

  case DOCUMENT_BULK_TAGS_RESPONSE: {
    const s = state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.map(sentence => {
        const actionSentence = _.find(action.sentences, s => sentence.get('uuid') === s.uuid);
        if (actionSentence) {
          return sentence.set('annotations', actionSentence.annotations)
        }
        return sentence;
      })
    );

    return s.merge({
      isBulkTagRequesting: false,
      bulkAnnotations: _getCommonAnnotations(
        s.get('analysis')
          .get('sentences')
          .filter(x => state.get('selectedSentences').indexOf(x.get('idx')) !== -1)
          .toJS()
      )
    });
  }

  case DOCUMENT_WHOLE_CHANGED_SOCKET: {
    return state.merge(action.data);
  }

  case SET_LOCK: {
    return state.update('locks', locks => locks.add(action.idx))
  }

  case UN_SET_LOCK: {
    return state.update('locks', locks => locks.remove(action.idx))
  }

  case FINISHED_RELEASING: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.idx),
        x => x.merge({
          isRequesting: false,
          isReleasing: false,
          releaseRetries: 0
        })  // Merging the given sentence
      )
    )
  }

  case FINISHED_REQUESTING: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.idx),
        x => x.merge({
          isRequesting: false,
          requestRetries: 0
        })  // Merging the given sentence
      )
    )
  }

  case ADD_COMMENT: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.idx),
        sentence => sentence.update(
          'comments',
          comments => comments.push(Map(action.comment))
        ).merge({
          comments_count: sentence.get('comments').count()
        })
      )
    )
  }

  case DELETE_COMMENT_SUCCESS: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => x.get('idx') === action.idx),
        sentence => sentence.update(
          'comments',
          comments => comments.filter(comment => {
            return comment.get('uuid') !== action.uuid
          })
        ).merge({
          comments_count: sentence.get('comments').count()
        })
      )
    )
  }

  case SUBMIT_EDIT_SENTENCE_SUCCESS: {
    return state.updateIn(
      ['analysis', 'sentences'],
      sentences => sentences.update(
        sentences.findIndex(x => {
          return x.get('idx') === action.idx
        }),
        x => x.merge(action.sentence)
      )
    )
  }
  case LIKE_SENTENCE_REQUEST: {
    return state;
  }

  case CLEAR_LIKE_SENTENCE_REQUEST: {
    return state;
  }

  case DISLIKE_SENTENCE_REQUEST: {
    return state;
  }

  case CLEAR_DISLIKE_SENTENCE_REQUEST: {
    return state;
  }

  case ADD_TAG_REQUEST: {
    return state;
  }

  case DELETE_TAG_REQUEST: {
    return state;
  }

  case ADD_BULK_TAG_REQUEST: {
    return state.merge({
      isBulkTagRequesting: true,
      bulkAnnotations: state
        .get('bulkAnnotations')
        .push({
          ... action.annotations[0],
          name: action.annotations[0] && action.annotations[0].label
        })
        .sortBy(x => x.label)
    });
  }

  case DELETE_BULK_TAG_REQUEST: {
    return state.merge({
      isBulkTagRequesting: true,
      bulkAnnotations: state
        .get('bulkAnnotations')
        .filter(x => x.get('label') !== (action.annotations[0] && action.annotations[0].label))
    });
  }

  case APPROVE_SUGGESTED_TAG_REQUEST: {
    return state;
  }

  case ASSIGN_SENTENCES_REQUEST: {
    return state;
  }

  case PREPARE_DOCUMENT_EXPORT_REQUEST: {
    return state;
  }

  case TOGGLE_DISPLAY_COMPONENT_BOOLEAN: {
    return state.set(
      action.key,
      typeof action.value === 'boolean' ?
      action.value :
      {
        ... state.get(action.key),
        ... action.value
      }
    );
  }

  case APPROVE_BULK_TAG_REQUEST: {
    return state.merge({
      isBulkTagRequesting: true
    });
  }

  case DOCUMENT_REANALYZE: {
    return state.merge({
      isInitialized: false,
      analysis: Map({
        parties: Map({
          you: Map({}),
          them: Map({})
        }),
        sentences: List(),
      }),
    });
  }

  case UPDATE_SELECTED_SENTENCES: {
    return state.merge({
      selectedSentences: action.selectedSentences,
      bulkAnnotations: _getCommonAnnotations(
        state
          .get('analysis')
          .get('sentences')
          .filter(x => action.selectedSentences.indexOf(x.get('idx')) !== -1)
          .toJS()
      )
    })
  }

  case GET_LEARNERS_SUCCESS : {
    //hardcoded default learner colors
    action.learners.push({ name:'RESPONSIBILITY',color_code:'#ffd4dc' });
    action.learners.push({ name:'TERMINATION',color_code:'#ffffb3' });
    action.learners.push({ name:'LIABILITY',color_code:'#b6daf2' });
    return state.merge({
      areLearnersInitialized: true,
      learners: action.learners
    });
  }

  default: {
    return state;
  }
  }
};
