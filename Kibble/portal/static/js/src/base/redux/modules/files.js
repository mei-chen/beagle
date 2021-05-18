import {
  getFromServer,
  patchToServer,
  postToServer
} from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  POST_ERROR,
  PATCH_REQUEST,
  PATCH_SUCCESS,
  PATCH_ERROR,
  LIST_CLEANUP,
  LIST_APPEND,
  LIST_PROGRESS,
  MODAL_SHOW,
  MODAL_HIDE
} from 'base/redux/actions';
import { formDataFrom } from 'base/utils/misc';

const ENDPOINT = window.CONFIG.API_URLS.fileList;

// Files request
const getFileRequest = () => {
  return {
    type: GET_REQUEST('file')
  };
}

const postFileRequest = () => {
  return {
    type: POST_REQUEST('file')
  };
}

const postFileSuccess = (data) => {
  return {
    type: POST_SUCCESS('file'),
    data
  };
}

const postFileError = (err) => {
  return {
    type: POST_ERROR('file'),
    err
  };
}

const getFileSuccess = (data, extra) => {
  const type = (extra) ? GET_SUCCESS(extra.type) : GET_SUCCESS('file');
  const key = (extra) ? extra.key : undefined;
  return {
    type,
    key,
    data
  };
}

const getFileError = (err) => {
  return {
    type: GET_ERROR('file'),
    err
  };
}

export const getFiles = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT, data, getFileRequest, getFileSuccess, getFileError, extra);
}

export const patchFile = (endpoint, data, successAction=postFileSuccess,
                             errorAction=postFileError) => {
  return patchToServer({
    endpoint, data, processEvent: postFileRequest,
    successEvent: successAction, errorEvent: errorAction
  });
}


export function getFilesForBatch(batch, module_name, non_converted = false) {
  return dispatch => {
    const data = { batch };
    if (non_converted) {
      data.nodocuments = true
    }
    dispatch(getFiles(
      data,
      { type: 'filesForBatch' + module_name, key: 'batch_files' }));
  }
}

export function showFilesPopup() {
  return (dispatch) => dispatch({
    type: MODAL_SHOW('file')
  });
}

export function hideFilesPopup() {
  return (dispatch) => dispatch({
    type: MODAL_HIDE('file')
  });
}

export function clearModalFilesList() {
  return (dispatch) => dispatch({
    type: LIST_CLEANUP('file')
  });
}

export function appendModalFilesList(file) {
  return (dispatch) => dispatch({
    type: LIST_APPEND('file'),
    data: file
  });
}

export function updateFileProgress(file, progress, error=null) {
  return (dispatch) => dispatch({
    type: LIST_PROGRESS('file'),
    data: {...file, progress: progress, error: error}
  })
}

/**
 * Fire multiple post request to a single url
 * Will make request like { key: value of values, ...inject }
 * @param {string} key, dict key for each item in iterable param
 * @param {Object||Array} values, FileList
 * @param {Object=} inject, this data will be injected into each request
 * @param {function} dispatch
 * @returns {Promise}
 */
export const multipleFileUpload = ({ dispatch, key, values, inject }) => {
  return new Promise((resolve, reject) => {
    const requestList = [];
    const headers = { 'Content-Type': 'multipart/form-data;boundary=BoUnDaRyStRiNg' };

    try {
      for (const item of values) {
        if (item.size && item.size > window.CONFIG.MAX_UPLOAD_SIZE) {
          reject(`File size is bigger then ${window.CONFIG.MAX_UPLOAD_SIZE} (${item.size}).`);
          return;
        }
        requestList.push({ [key]: item, ...inject })
      }
    } catch (e) {
      reject('File was not provided.');
    }

    for (const requestData of requestList) {
      dispatch(postToServer({
        endpoint: ENDPOINT,
        data: formDataFrom(requestData),
        successEvent: (r) => updateFileProgress({ name: requestData[ key ].name}, 100),
        errorEvent: (e) => updateFileProgress({
          name: requestData[ key ].name},
          0,
          e.data && e.data.non_field_errors || e.message || e.data.detail || 'Upload error',
        ),
        headers,
        config: {
          onUploadProgress: function(progressEvent) {
            let percentCompleted = Math.round( (progressEvent.loaded * 100) / progressEvent.total )
            // Dispatch
            updateFileProgress({name: requestData[ key ].name}, percentCompleted)
          }
        }
      }))
    }

    resolve('ok')
  })
};


// REDUCERS
const initialState = {
  list: [],
  popup: false
};


export default (state = initialState, action = {}) => {
  switch (action.type) {

    case GET_SUCCESS('file'):
    {
      return {
        ...state,
        ...action.data
      };
    }

    case MODAL_SHOW('file'):
    {
      return {
        ...state,
        popup: true
      };
    }

    case MODAL_HIDE('file'):
    {
      return {
        ...state,
        popup: false
      };
    }

    case LIST_CLEANUP('file'):
    {
      return {
        ...state,
        list: []
      };
    }

    case LIST_APPEND('file'):
    {
      return {
        ...state,
        list: state.list.concat([ action.data ]),
      };
    }

    case LIST_PROGRESS('file'):
    {
      // Add file if not there and update progress
      let list = []
      let added = false
      for (let i = 0; i < state.list.length; i++) {
        if (state.list[i].name == action.data.name) {
          list.push({...state.list[i], progress: action.data.progress, error: error})
          added = true
        } else {
          list.push({...state.list[i]})
        }
      }

      if (!added) {
        list.push({...action.data})
      }

      return {
        ...state,
        list: list
      }
      
    }

    default:
    {
      return state;
    }
  }
};
