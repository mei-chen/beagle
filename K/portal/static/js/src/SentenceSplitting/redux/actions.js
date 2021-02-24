import { 
  SSAPI_POST, CLEAR_WS_MESSAGE, BULK_DOWNLOAD_TASK_STATE, CLEAR_BULK_DOWNLOAD_URL
} from 'SentenceSplitting/redux/constants';

export function populateLockedDocuments(data) {
  return dispatch => dispatch({
    type: SSAPI_POST, data
  })
}

export function clearWsMessage() {
  return dispatch => dispatch({
    type: CLEAR_WS_MESSAGE
  })
}

export function bulkDownloadTaskSetState(data) {
  return dispatch => dispatch({
    type: BULK_DOWNLOAD_TASK_STATE, data
  })
}

export function clearBulkDownloadUrl() {
  return dispatch => dispatch({
    type: CLEAR_BULK_DOWNLOAD_URL
  })
}
