import axios from 'axios';
import { Map, List, fromJS } from 'immutable';
import qs from 'qs';

import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'preview_module';

// ACTION CONSTANTS
const GET_PREVIEW_REQEUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_PREVIEW_REQEUEST`;
const GET_PREVIEW_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_PREVIEW_SUCCESS`;
const GET_PREVIEW_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_PREVIEW_ERROR`;
const GET_DATASET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_DATASET_REQUEST`;
const GET_DATASET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_DATASET_SUCCESS`;
const SET_MAPPING = `${MODULE_NAME}/${CURRENT_NAME}/SET_MAPPING`;
export const CLEAR_EVALUATION = `${MODULE_NAME}/${CURRENT_NAME}/CLEAR_EVALUATION`;
const SET_SPLIT_STATUS = `${MODULE_NAME}/${CURRENT_NAME}/SET_SPLIT_STATUS`;

const URL_BASE = '/api/v1/evaluate/';

const getDatasetUrl = id => `/api/v1/dataset/${id}/`;
const getPreviewUrl = id => `/api/v1/dataset/${id}/preview/`;
const getCacheUrl = id => `/api/v1/experiment/${id}/get_evaluate_data/`;
const getSaveCacheUrl = id => `/api/v1/experiment/${id}/set_evaluate_data/`;

// ACTION CREATORS
const getPreiviewRequest = () => ({ type: GET_PREVIEW_REQEUEST });

const getPreviewSuccess = data => ({ type: GET_PREVIEW_SUCCESS, data });

const getPreviewError = data => ({ type: GET_PREVIEW_ERROR, data });

const getDatasetRequest = () => ({ type: GET_DATASET_REQUEST });

const getDatasetSuccess = data => ({ type: GET_DATASET_SUCCESS, data });

const setMapping = mapping => ({ type: SET_MAPPING, mapping });

export const clearEvaluation = () => ({ type: CLEAR_EVALUATION });

export const setSplitStatus = status => ({ type: SET_SPLIT_STATUS, status })

// Async actions
export const addDataset = dataset => dispatch => {
  dispatch(setMapping(dataset.mapping));
  return dispatch(getDatasetFromServer(dataset.id))
};

export const getPreviewFromServer = (id, mapping, split) => dispatch => {
  dispatch(getPreiviewRequest());
  return axios.post(getPreviewUrl(id), { mapping, split })
    .then(response => {
      dispatch(getPreviewSuccess(response.data))
    }).catch(err => {
      if(err.response.status === 400) dispatch(getPreviewError(err.response.data[0]))
      handleError();
    });
};

const getDatasetFromServer = id => dispatch => {
  dispatch(getDatasetRequest());
  return axios.get(getDatasetUrl(id))
    .then(res => {
      dispatch(getDatasetSuccess(res.data))
    })
    .catch(handleError);
};

export const getCachedData = (id) => dispatch => {
  return axios.get(getCacheUrl(id))
};

export const setCachedData = (id, data) => dispatch => {
  return axios.post(getSaveCacheUrl(id), data)
};

// HELPERS
const handleError = err => {
  console.error(err.response || err);
  throw err;
}

// REDUCERS
const initialState = Map({
  isInitialized: false,
  dataset: new Map(),
  mapping: new Map(),
  samples: new List(),
  stats: new Map(),
  isSplit: true,
  previewError: ''
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_DATASET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      dataset: action.data
    })
  }

  case SET_MAPPING: {
    return state.set('mapping', fromJS(action.mapping))
  }

  case GET_PREVIEW_REQEUEST: {
    return state.set('previewError', '')
  }

  case GET_PREVIEW_SUCCESS: {
    return state.merge({
      samples: fromJS(action.data.results),
      stats: Map(action.data.stats)
    })
  }

  case GET_PREVIEW_ERROR: {
    return state.set('previewError', action.data)
  }

  case CLEAR_EVALUATION: {
    return initialState;
  }

  case SET_SPLIT_STATUS: {
    return state.set('isSplit', action.status)
  }

  default: {
    return state
  }
  }
};
