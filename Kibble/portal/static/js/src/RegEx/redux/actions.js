import * as RegExConstants from 'RegEx/redux/constants';

export function setModalOpen(modal, isOpen) {
  return dispatch => dispatch({
    type: RegExConstants.SET_MODAL_OPEN,
    data: { modal, isOpen }
  });
}

export function setSelectedRegEx(data) {
  return dispatch => dispatch({
    type: RegExConstants.REGEX_SELECT,
    data
  });
}

export function deselectRegEx() {
  return dispatch => dispatch({ type: RegExConstants.REGEX_DESELECT });
}

export function setSelectedBatchId(data) {
  return dispatch => dispatch({ type: RegExConstants.BATCH_SELECT, data })
}

export function setSelectedProjectId(data) {
  return dispatch => dispatch({ type: RegExConstants.PROJECT_SELECT, data })
}

export function setSelectedReport(uuid) {
  return dispatch => dispatch({ type: RegExConstants.REPORT_SELECT, uuid })
}


export function bulkDownloadTaskSetState(data) {
  return dispatch => dispatch({
    type: RegExConstants.BULK_DOWNLOAD_TASK_STATE, data
  })
}

export function clearBulkDownloadUrl() {
  return dispatch => dispatch({
    type: RegExConstants.CLEAR_BULK_DOWNLOAD_URL
  })
}
