import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// APP CONSTANTS
import { MODULE_NAME } from '../constants';
const CURRENT_NAME = 'labeling_module';

const ASSIGNMENTS_URL = '/api/v1/assignment/';

// ACTION CONSTANTS
const GET_ASSIGNMENT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_ASSIGNMENT_REQUEST`;
const GET_ASSIGNMENT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_ASSIGNMENT_SUCCESS`;
const GET_SAMPLES_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_SAMPLES_REQUEST`;
const GET_SAMPLES_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SAMPLES_SUCCESS`;
const POST_SAMPLES_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/POST_SAMPLES_REQUEST`;
const POST_SAMPLES_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/POST_SAMPLES_SUCCESS`;
const BUILD_EXPERIMENT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/BUILD_EXPERIMENT_REQUEST`;
const BUILD_EXPERIMENT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/BUILD_EXPERIMENT_SUCCESS`;
const SET_LABEL = `${MODULE_NAME}/${CURRENT_NAME}/SET_LABEL`;
const SET_SKIPPED = `${MODULE_NAME}/${CURRENT_NAME}/SET_SKIPPED`;

// URL getters
const getAssignmentUrl = id => `${ASSIGNMENTS_URL}${id}`;
const getSamplesStartUrl = id => `${ASSIGNMENTS_URL}${id}/start_stage/`;
const getSamplesFinishUrl = id => `${ASSIGNMENTS_URL}${id}/finish_stage/`;
const getBuildExperimentUrl = id => `${ASSIGNMENTS_URL}${id}/build_experiment/`;

// ACTION CREATORS
const getAssignmentRequest = () => ({ type: GET_ASSIGNMENT_REQUEST });

const getAssignmentSuccess = data => ({ type: GET_ASSIGNMENT_SUCCESS, data });

const getSamplesRequest = getTaskUuid => ({ type: GET_SAMPLES_REQUEST, getTaskUuid });

export const getSamplesSuccess = data => ({ type: GET_SAMPLES_SUCCESS, data });

const postSamplesRequest = postTaskUuid => ({ type: POST_SAMPLES_REQUEST, postTaskUuid });

export const postSamplesSuccess = () => ({ type: POST_SAMPLES_SUCCESS });

const buildExperimentRequest = buildExperimentTaskUuid => ({ type: BUILD_EXPERIMENT_REQUEST, buildExperimentTaskUuid });

export const buildExperimentSuccess = data => ({ type: BUILD_EXPERIMENT_SUCCESS, data });

export const setLabel = (index, label) => ({ type: SET_LABEL, index, label });

export const setSkipped = index => ({ type: SET_SKIPPED, index });

export const getAssignmentFromServer = id => dispatch => {
  dispatch(getAssignmentRequest());
  return axios
    .get(getAssignmentUrl(id))
    .then(res => {
      dispatch(getAssignmentSuccess(res.data))
      return res;
    })
    .catch(handleError);
};

export const getSamplesFromServer = (getTaskUuid, id) => dispatch => {
  dispatch(getSamplesRequest(getTaskUuid));
  return axios
    .post(getSamplesStartUrl(id), { task_uuid: getTaskUuid }) // results got in sockets
    .catch(handleError);
};

export const postSamplesToServer = (postTaskUuid, id, samples) => (dispatch, getState) => {
  dispatch(postSamplesRequest(postTaskUuid));
  return axios
    .post(getSamplesFinishUrl(id), { samples, task_uuid: postTaskUuid })
    .then(dispatch(postSamplesSuccess()))
    .catch(handleError);
};

export const buildExperimentOnServer = (buildExperimentTaskUuid, id) => (dispatch, getState) => {
  dispatch(buildExperimentRequest(buildExperimentTaskUuid));
  return axios
    .post(getBuildExperimentUrl(id), { task_uuid: buildExperimentTaskUuid }) // results will be handles by socket client
    .catch(handleError);
};

// HELPERS
const handleError = err => {
  console.error(err.response || err);
  throw err;
};

const apiData = Type => {
  return Map({
    isLoading: false,
    isError: false,
    data: Type()
  })
};

const processData = Type => {
  return Map({
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: Type()
  })
};

// REDUCERS
const initialState = Map({
  stage: null,
  getTaskUuid: null, // celery task (not labeling task)
  postTaskUuid: null,
  buildExperimentTaskUuid: null,
  assignment: apiData(Map),
  samples: apiData(List),
  buildingExperiment: processData(Map),
  stats: Map()
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_ASSIGNMENT_REQUEST: {
    return state.set('assignment', Map({
      isLoading: true,
      isError: false,
      data: Map()
    }));
  }

  case GET_ASSIGNMENT_SUCCESS: {
    return state.set('assignment', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data)
    }));
  }

  case GET_SAMPLES_REQUEST: {
    return state.set('samples', Map({
      isLoading: true,
      isError: false,
      data: List()
    }))
    .set('getTaskUuid', action.getTaskUuid)
    .set('stats', Map());
  }

  case GET_SAMPLES_SUCCESS: {
    // if 'selecting samples' task (get task) was run in different window
    if(action.data.task_uuid !== state.get('getTaskUuid')) return state;

    return state.set('samples', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data.samples)
    }))
    .set('stage', action.data.stage)
    .set('stats', Map(action.data.stats));
  }

  case POST_SAMPLES_REQUEST: {
    return state.set('postTaskUuid', action.postTaskUuid)
  }

  case SET_LABEL: {
    return state.updateIn(['samples', 'data', action.index], sample => sample.set('label', action.label).remove('skipped'))
  }

  case SET_SKIPPED: {
    return state.updateIn(['samples', 'data', action.index], sample => sample.set('skipped', true).remove('label'))
  }

  case BUILD_EXPERIMENT_REQUEST: {
    return state.set('buildingExperiment', Map({
      isLoading: true,
      isError: false,
      isSuccess: false
    }))
    .set('buildExperimentTaskUuid', action.buildExperimentTaskUuid)
  }

  case BUILD_EXPERIMENT_SUCCESS: {
    return state.set('buildingExperiment', Map({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: fromJS(action.data)
    }));
  }

  default: {
    return state
  }
  }
};
