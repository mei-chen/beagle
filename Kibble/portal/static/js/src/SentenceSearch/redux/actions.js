import * as SentenceSearchConstants from 'SentenceSearch/redux/constants';

export function setModalOpen(modal, isOpen) {
  return dispatch => dispatch({
    type: SentenceSearchConstants.SET_MODAL_OPEN,
    data: { modal, isOpen }
  });
}

export function changeSentenceInput(sentence) {
  return dispatch => dispatch({
    type: SentenceSearchConstants.CHANGE_SENTENCE_INPUT,
    sentence: sentence
  })
}

export function setSelectedBatchId(data) {
  return dispatch => dispatch({ type: SentenceSearchConstants.BATCH_SELECT, data })
}

export function setSelectedProjectId(data) {
  return dispatch => dispatch({ type: SentenceSearchConstants.PROJECT_SELECT, data })
}

export function addNewKeyword(word) {
  return dispatch => dispatch({
    type: SentenceSearchConstants.KEYWORD_ADD,
    word
  });
}

export function setSelectedReport(uuid) {
  return dispatch => dispatch({ type: SentenceSearchConstants.REPORT_SELECT, uuid })
}


export function bulkDownloadTaskSetState(data) {
  return dispatch => dispatch({
    type: SentenceSearchConstants.BULK_DOWNLOAD_TASK_STATE, data
  })
}

export function clearBulkDownloadUrl() {
  return dispatch => dispatch({
    type: SentenceSearchConstants.CLEAR_BULK_DOWNLOAD_URL
  })
}
