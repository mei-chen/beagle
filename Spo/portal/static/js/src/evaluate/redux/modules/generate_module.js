import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

import { MODULE_NAME } from '../constants';
import { CLEAR_EVALUATION } from './preview_module';

const CURRENT_NAME = 'generate_module';

// ACTION CONSTANTS
const GENERATE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GENERATE_REQUEST`;
const GENERATE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GENERATE_SUCCESS`;
const QUIT_GENERATION = `${MODULE_NAME}/${CURRENT_NAME}/QUIT_GENERATION`;

const URL_BASE = '/api/v1/experiment/';

const getGenerateUrl = id => `${URL_BASE}${id}/generate/`;

// ACTION CREATORS
const generateRequest = taskUuid => ({ type: GENERATE_REQUEST, taskUuid });

export const generateSuccess = data => ({ type: GENERATE_SUCCESS, data });

export const quitGeneration = data => ({ type: QUIT_GENERATION, data })

// Async actions
export const generateOnServer = (taskUuid, id, data) => dispatch => {
  dispatch(generateRequest(taskUuid));
  return axios.post(getGenerateUrl(id), { task_uuid: taskUuid, ...data })
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
  isGenerating: false,
  taskUuid: null,
  samples: new List(),
  stats: new Map(),
  generationError: ''
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GENERATE_REQUEST: {
    return state.merge({
      isGenerating: true,
      taskUuid: action.taskUuid,
      generationError: ''
    })
  }

  case GENERATE_SUCCESS: {
    // if this task was run in different window
    if(action.data.task_uuid !== state.get('taskUuid')) return state;

    return state.merge({
      isInitialized: true,
      isGenerating: false,
      samples: fromJS(action.data.preview.results),
      stats: Map(action.data.preview.stats)
    })
  }

  case QUIT_GENERATION: {
    // if this task was run in different window
    if(action.data.task_uuid !== state.get('taskUuid')) return state;

    return state.merge({
      generationError: action.data.error,
      isGenerating: false
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
