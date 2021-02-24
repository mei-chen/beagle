import axios from 'axios';
import { Map, fromJS } from 'immutable';

import { MODULE_NAME } from '../constants';
import { CLEAR_EVALUATION } from './preview_module'

const CURRENT_NAME = 'evaluate_module';

// ACTION CONSTANTS
const EVALUATE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/EVALUATE_REQUEST`;
const EVALUATE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/EVALUATE_SUCCESS`;
const QUIT_EVALUATION = `${MODULE_NAME}/${CURRENT_NAME}/QUIT_EVALUATION`;

const URL_BASE = '/api/v1/experiment/';

const getEvaluateUrl = id => `${URL_BASE}${id}/evaluate/`;

// ACTION CREATORS
const evaluateRequest = taskUuid => ({ type: EVALUATE_REQUEST, taskUuid });

export const evaluateSuccess = data => ({ type: EVALUATE_SUCCESS, data });

export const quitEvaluation = data => ({ type: QUIT_EVALUATION, data });

// Async actions
export const evaluateOnServer = (taskUuid, id, data) => dispatch => {
  dispatch(evaluateRequest(taskUuid))
  return axios.post(getEvaluateUrl(id), { task_uuid: taskUuid, ...data })
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
  isEvaluating: false,
  taskUuid: null,
  scores: new Map(),
  evaluationError: ''
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case EVALUATE_REQUEST: {
    return state.merge({
      isEvaluating: true,
      taskUuid: action.taskUuid,
      evaluationError: ''
    })
  }

  case EVALUATE_SUCCESS: {
    // if this task was run in different window
    if(action.data.task_uuid !== state.get('taskUuid')) return state;

    return state.merge({
      isInitialized: true,
      isEvaluating: false,
      scores: new Map(action.data.scores)
    })
  }

  case QUIT_EVALUATION: {
    // if this task was run in different window
    if(action.data.task_uuid !== state.get('taskUuid')) return state;

    return state.merge({
      evaluationError: action.data.error,
      isEvaluating: false
    });
  }

  case CLEAR_EVALUATION: {
    return initialState;
  }

  default: {
    return state
  }
  }
};
