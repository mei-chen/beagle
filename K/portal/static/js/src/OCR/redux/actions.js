import * as ocrConstants from 'OCR/redux/constants'

export function setTaskState(value) {
  return dispatch => dispatch({ type: ocrConstants.TASK_STATE, value })
}

export function addProcessingFiles(payload) {
  return dispatch => dispatch({
    type: ocrConstants.ADD_PROCESSING_FILES,
    payload
  })
}

export function clearProcessingFiles(payload) {
  return dispatch => dispatch({ type: ocrConstants.CLEAR_PROCESSING_FILES })
}

export function updateBatch(payload) {
  return dispatch => dispatch({ type: ocrConstants.UPDATE_BATCH, payload })
}

export function insertBatch(payload) {
  return dispatch => dispatch({ type: ocrConstants.INSERT_BATCH, payload })
}

export function clearAlert() {
  return dispatch => dispatch({ type: ocrConstants.CLEAR_ALERT })
}
