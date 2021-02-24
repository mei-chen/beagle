import { List } from 'immutable';
import {
  getFromServer,
  postToServer,
  patchToServer,
  deleteOnServer
} from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  PATCH_SUCCESS,
  POST_ERROR,
  DELETE_REQUEST,
  DELETE_SUCCESS,
  DELETE_ERROR
} from 'base/redux/actions';
import { PROJECT_STATUS } from 'base/redux/constants';

const ENDPOINT = window.CONFIG.API_URLS.batchList;

// projects request
const getBatchRequest = () => {
  return {
    type: GET_REQUEST('batch')
  };
};

const getBatchSuccess = (data, extra) => {
  const type = (extra) ? GET_SUCCESS(extra.type) : GET_SUCCESS('batch');
  const key = (extra) ? extra.key : undefined;
  return {
    type,
    key,
    data
  };
};

const getBatchError = (err) => {
  return {
    type: GET_ERROR('batch'),
    err
  };
};

const postBatchRequest = () => {
  return {
    type: POST_REQUEST('batch')
  };
};

const postBatchSuccess = (data) => {
  return {
    type: POST_SUCCESS('batch'),
    data
  };
};

const postBatchError = (err) => {
  return {
    type: POST_ERROR('batch'),
    err
  };
};

const deleteBatchRequest = () => {
  return {
    type: DELETE_REQUEST('batch')
  };
};

const deleteBatchSuccess = (id) => {
  return {
    type: DELETE_SUCCESS('batch'),
    id
  };
};

const deleteBatchError = (err) => {
  return {
    type: DELETE_ERROR('batch'),
    err
  };
};

export const getBatches = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT, data, getBatchRequest, getBatchSuccess, getBatchError, extra);
};

export const postBatches = (data, successEvent = postBatchSuccess,
                            errorEvent = postBatchError) => {
  return postToServer({
    endpoint: ENDPOINT,
    data,
    successEvent,
    errorEvent
  });
};

export const deleteBatch = (id) => {
  return deleteOnServer({
    endpoint: `${ENDPOINT}${id}`,
    processEvent: deleteBatchRequest,
    successEvent: () => deleteBatchSuccess(id),
    errorEvent: getBatchError
  });
};


export const patchBatch = (endpoint, data, successAction = postBatchSuccess,
                           errorAction = postBatchError, callbacks) => {
  return patchToServer({
    endpoint,
    data,
    processEvent: postBatchRequest,
    successEvent: successAction,
    errorEvent: errorAction,
    callbacks
  })
};

export function getBatchForProject(project, module_name, all=false) {
  return dispatch => {
    dispatch(getBatches(
      all ? {} : {project}, {
        type: 'batchForProject' + module_name, key: 'project_batches'
    }));
  }
}

export function getCollaboratorsForBatch(id) {
  console.log(ENDPOINT);
}

// REDUCERS
const initialState = List();


export default (state = initialState, action) => {
  switch (action.type) {

    case GET_SUCCESS('batch'):
      return List(action.data);

    case POST_SUCCESS('batch'):
      return state.push(action.data);

    case PATCH_SUCCESS('batch'):
      return state.map((obj) => {
        if (obj.resource_uri === action.response.resource_uri) {
          return action.response
        }
        return obj
      });

    case DELETE_SUCCESS('batch'):
      return state.filter(batch => batch.id !== action.id)

    default:
    {
      return state;
    }
  }
};
