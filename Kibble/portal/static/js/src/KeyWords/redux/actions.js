import * as KeyWordsConstants from 'KeyWords/redux/constants';

export function setModalOpen(modal, isOpen) {
  return dispatch => dispatch({
    type: KeyWordsConstants.SET_MODAL_OPEN,
    data: { modal, isOpen }
  });
}

export function setCurrentWord(word) {
  return dispatch => dispatch({
    type: KeyWordsConstants.INPUT_WORD,
    word
  });
}

export function selectSimModel(data) {
    return dispatch => dispatch({
      type: KeyWordsConstants.SELECT_SIMMODEL,
      data
    });
}

export function markRecommendation(index) {
  return dispatch => dispatch({
    type: KeyWordsConstants.MARK_RECOMMENDATION,
    index
  });
}

export function markSynonym(index) {
  return dispatch => dispatch({
    type: KeyWordsConstants.MARK_SYNONYM,
    index
  });
}

export function markManual(index) {
  return dispatch => dispatch({
    type: KeyWordsConstants.MARK_MANUAL,
    index
  });
}

export function purge() {
  return dispatch => dispatch({
    type: KeyWordsConstants.PURGE
  });
}

export function selectKeywordList(data) {
  return dispatch => dispatch({
    type: KeyWordsConstants.KEYWORDLIST_SELECT,
    data
  });
}

export function deselectKeywordList() {
  return dispatch => dispatch({ type: KeyWordsConstants.KEYWORDLIST_DESELECT });
}


export function setSelectedBatchId(data) {
  return dispatch => dispatch({ type: KeyWordsConstants.BATCH_SELECT, data })
}

export function setSelectedProjectId(data) {
  return dispatch => dispatch({ type: KeyWordsConstants.PROJECT_SELECT, data })
}

export function addNewKeyword(word) {
  return dispatch => dispatch({
    type: KeyWordsConstants.KEYWORD_ADD,
    word
  });
}

export function setSelectedReport(uuid) {
  return dispatch => dispatch({ type: KeyWordsConstants.REPORT_SELECT, uuid })
}


export function bulkDownloadTaskSetState(data) {
  return dispatch => dispatch({
    type: KeyWordsConstants.BULK_DOWNLOAD_TASK_STATE, data
  })
}

export function clearBulkDownloadUrl() {
  return dispatch => dispatch({
    type: KeyWordsConstants.CLEAR_BULK_DOWNLOAD_URL
  })
}

export function changeExcludeCheckmark() {
  return dispatch => dispatch({
    type: KeyWordsConstants.CHANGE_EXCLUDE
  })
}
