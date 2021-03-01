import * as SentencesObfuscationConstants from 'SentencesObfuscation/redux/constants'
import axios from 'axios';
const DOCS_ENDPOINT = window.CONFIG.API_URLS.docList;


export function resetReportsLists() {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.RESET_REPORTS_LISTS
  });
}

export function handleReportSelect(id) {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.SELECT_REPORT,
    id: id
  });
}

export function handleReportUnSelect(id) {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.UNSELECT_REPORT,
    id: id
  });
}

export function setModalOpen(state) {
	return dispatch => dispatch({
		type: SentencesObfuscationConstants.SET_MODAL_OPEN,
		state: state
	})
}

export function markSentence(rep_id, sent_idx, method) {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.MARK_SENTENCE,
    rep_id: rep_id,
    sent_idx: sent_idx,
    method: method
  })
}

export function markAllSentences(data) {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.MARK_ALL_SENTENCES,
    data: data
  })
}

export function cancelLabeling() {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.CANCEL_LABELING
  })
}

export function doneLabeling() {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.DONE_LABELING
  })
}

export function getDocsForBatchSuccess(data) {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.DOCS_SUCCESS,
    data: data
  })
}

export function getDocsForBatchReq() {
  return dispatch => dispatch({
    type: SentencesObfuscationConstants.DOCS_REQ,
  })
}

export const getDocsFromServer = (batch) => {
  const params = {source_file__batch: batch, isorigin: true}
  return (dispatch) => {
    dispatch(getDocsForBatchReq());
    return axios.get(DOCS_ENDPOINT,{ params })
      .then((response) => {
        dispatch(getDocsForBatchSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  };
};