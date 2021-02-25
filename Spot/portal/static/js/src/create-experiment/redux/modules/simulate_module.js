import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';
import { DO_HISTORY } from './create_experiment_module'

const CURRENT_NAME = 'simulate_module';

// ACTION CONSTANTS
const POST_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/POST_REQUEST`;
const POST_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/POST_SUCCESS`;
const RESET = `${MODULE_NAME}/${CURRENT_NAME}/RESET`;

// URLS
const URL_BASE = '/api/v1/experiment/';
const getSimulateUrl = id => `${URL_BASE}${id}/simulate/`

// ACTION CREATORS
export const postRequest = taskUuid => {
  return {
    type: POST_REQUEST,
    taskUuid
  }
};

export const postSuccess = data => {
  return {
    type: POST_SUCCESS,
    data
  }
};

export const reset = () => {
  return {
    type: RESET
  }
};


export const simulateOnServer = (taskUuid, id, sample) => {
  return (dispatch, getState) => {
    dispatch(postRequest(taskUuid))
    return axios.post(getSimulateUrl(id), { task_uuid: taskUuid, sample })
      .catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// INITIAL STATE
const initialState = Map({
  isSimulating: false,
  isSimulatedFormulaDirty: true,
  status: null,
  sample: new List(),
  resultsPerClassifier: new List(),
  confidence: null,
  taskUuid: null
});

// REDUCERS
export default (state=initialState, action={}) => {
  switch (action.type) {

  case POST_REQUEST: {
    return state.merge({
      status: null,
      isSimulating: true,
      taskUuid: action.taskUuid,
      sample: new List(),
      confidence: null
    });
  }

  case POST_SUCCESS: {
    // if this task was run in different window
    if(action.data.task_uuid !== state.get('taskUuid')) return state;

    return state.merge({
      status: action.data.results.status,
      confidence: action.data.results.confidence,
      sample: fromJS(action.data.results.sample),
      resultsPerClassifier: fromJS(action.data.results_per_classifier),
      isSimulating: false,
      isSimulatedFormulaDirty: false
    });
  }

  case RESET: {
    return initialState;
  }

  case DO_HISTORY: {
    return state.set('isSimulatedFormulaDirty', true)
  }

  default: {
    return state
  }
  }
};
