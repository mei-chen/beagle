import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'dataset_details_module';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const EDIT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_REQUEST`;
const EDIT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_SUCCESS`;
const GET_SAMPLES_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_SAMPLES_REQUEST`;
const GET_SAMPLES_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SAMPLES_SUCCESS`;
const EDIT_SAMPLE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_SAMPLE_REQUEST`;
const EDIT_SAMPLE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_SAMPLE_SUCCESS`;
const DELETE_SAMPLE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_SAMPLE_REQUEST`;
const DELETE_SAMPLE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_SAMPLE_SUCCESS`;
const SET_USED = `${MODULE_NAME}/${CURRENT_NAME}/SET_USED`;

// URLS
const URL_BASE = '/api/v1/dataset/';
const getSamplesUrl = (id, page, sortedBy, sortedDirection, filter) => {
  let url = `${URL_BASE}${id}/sample?page=${page}`;
  if(sortedBy) url += `&sortBy=${sortedBy}&order=${sortedDirection}`;
  if(filter) url += `&search=${filter}`;
  return url;
};
const getSampleUrl = (id, index) => `${URL_BASE}${id}/sample/${index}/`

const getDatasetUrl = (id) => `${URL_BASE}${id}/`

// ACTION CREATORS
const getRequest = () => ({ type: GET_REQUEST });

const getSuccess = data => ({ type: GET_SUCCESS, data });

const getSamplesRequest = () => ({ type: GET_SAMPLES_REQUEST });

const getSamplesSuccess = data => ({ type: GET_SAMPLES_SUCCESS, data });

const editSampleRequest = () => ({ type: EDIT_SAMPLE_REQUEST });

const editSampleSuccess = (id, index, data) => ({ type: EDIT_SAMPLE_SUCCESS });

const editRequest = () => ({ type: EDIT_REQUEST });

const editSuccess = data => ({ type: EDIT_SUCCESS, data });

const deleteSampleRequest = () => ({ type: DELETE_SAMPLE_REQUEST });

const deleteSampleSuccess = () => ({ type: DELETE_SAMPLE_SUCCESS });

export const setUsed = status => ({ type: SET_USED, status });

// Async actions
export const getFromServer = id => dispatch => {
  dispatch(getRequest());
  return axios.get(`${URL_BASE}${id}/`)
    .then(response => {
      dispatch(getSuccess(response.data))
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const getSamplesFromServer = (id, page, sortedBy, sortedDirection, filter) => dispatch => {
  dispatch(getSamplesRequest());
  return axios.get(getSamplesUrl(id, page, sortedBy, sortedDirection, filter))
    .then(response => {
      dispatch(getSamplesSuccess(response.data));
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const editSampleOnServer = (id, index, data) => dispatch => {
  dispatch(editSampleRequest());
  return axios.put(getSampleUrl(id, index), data)
    .then(response => {
      dispatch(editSampleSuccess())
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const editOnServer = (id, data) => dispatch => {
  dispatch(editRequest());
  return axios.put(getDatasetUrl(id), data)
    .then(response => {
      dispatch(editSuccess(response.data));
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const deleteSampleFromServer = (id, index) => dispatch => {
  dispatch(deleteSampleRequest());
  return axios.delete(getSampleUrl(id, index))
    .then(response => {
      dispatch(deleteSampleSuccess())
    })
    .catch((err) => {
      // delete not allowed error (labeling task is active)
      if(err.response.status === 405) dispatch(setUsed(true))
      console.error(err.response || err);
      throw err;
    });
};

// REDUCERS
const initialState = Map({
  datasetInitialized: false,
  samplesInitialized: false,
  dataset: new Map(),
  samples: new List(),
  count: 0,
  usedInLabelingTask: false
});


export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_SUCCESS: {
    return state.merge({
      datasetInitialized: true,
      dataset: fromJS(action.data)
    })
  }

  case EDIT_SUCCESS: {
    return state.merge({
      dataset: fromJS(action.data)
    })
  }

  case GET_SAMPLES_SUCCESS: {
    const samplesMap = fromJS(action.data.results);

    return state.merge({
      samplesInitialized: true,
      samples: samplesMap,
      count: action.data.count
    })
  }

  case SET_USED: {
    return state.set('usedInLabelingTask', action.status);
  }

  default: {
    return state
  }
  }
};
