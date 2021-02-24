import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

import { MODULE_NAME } from '../constants';
import { CLEAR_EVALUATION } from './preview_module';

const CURRENT_NAME = 'diff_module';

// ACTION CONSTANTS
const GET_DIFF_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_DIFF_REQUEST`;
const GET_DIFF_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_DIFF_SUCCESS`;
const GET_DIFF_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_DIFF_ERROR`;

const SIMULATE_DIFF_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/SIMULATE_DIFF_REQUEST`;
const SIMULATE_DIFF_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/SIMULATE_DIFF_SUCCESS`;

const URL_BASE = '/api/v1/diff_predicted/';

const getDiffUrl = (id, page) => `${URL_BASE}${id}?page=${page}`;
const getSimulateUrl = id => `/api/v1/experiment/${id}/simulate/`

// ACTION CREATORS
const getDiffRequest = () => ({ type: GET_DIFF_REQUEST });

const getDiffSuccess = data => ({ type: GET_DIFF_SUCCESS, data });

const getDiffError = data => ({ type: GET_DIFF_ERROR, data });

const simulateDiffRequest = taskUuid => ({ type: SIMULATE_DIFF_REQUEST, taskUuid });

export const simulateDiffSuccess = data => ({ type: SIMULATE_DIFF_SUCCESS, data });

// Async actions
export const getDiffFromServer = (id, page) => dispatch => {
  dispatch(getDiffRequest());
  return axios.get(getDiffUrl(id, page))
    .then(response => {
      dispatch(getDiffSuccess(response.data))
    })
    .catch(handleError);
};

export const simulateDiffOnServer = (taskUuid, id, sample) => dispatch => {
  dispatch(simulateDiffRequest(taskUuid))
  return axios.post(getSimulateUrl(id), { task_uuid: taskUuid, sample })
    .catch(handleError);
};

// HELPERS
const handleError = err => {
  console.error(err.response || err);
  throw err;
}

// REDUCERS
const initialState = Map({
  isInitialized: false,
  samples: new List(),
  count: 0,
  diffSimulations: new Map(),
  diffError: ''
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_DIFF_REQUEST: {
    return state.set('diffError', '')
  }

  case GET_DIFF_SUCCESS: {
    return state.merge({
      isInitialized: true,
      samples: fromJS(action.data.results),
      count: action.data.count
    })
  }

  case GET_DIFF_ERROR: {
    return state.set('diffError', action.data)
  }

  case CLEAR_EVALUATION: {
    return initialState;
  }

  case SIMULATE_DIFF_REQUEST: {
    return state.update('diffSimulations', diffSimulations => diffSimulations.set(action.taskUuid, new Map({
      isSimulating: true
    })))
  }

  case SIMULATE_DIFF_SUCCESS: {
    return state.update('diffSimulations', diffSimulations => diffSimulations.set(action.data.task_uuid, new Map({
      status: action.data.results.status,
      confidence: action.data.results.confidence,
      sample: fromJS(action.data.results.sample),
      resultsPerClassifier: fromJS(action.data.results_per_classifier),
      isSimulating: false
    })));
  }

  default: {
    return state
  }
  }
};
