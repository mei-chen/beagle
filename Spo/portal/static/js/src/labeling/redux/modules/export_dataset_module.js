import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// APP CONSTANTS
import { MODULE_NAME } from '../constants';
const CURRENT_NAME = 'export_dataset_module';

const TASKS_URL = '/api/v1/labeling_task/';

// ACTION CONSTANTS
const GET_TASK_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_TASK_REQUEST`;
const GET_TASK_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_TASK_SUCCESS`;
const GET_SCORES_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_SCORES_REQUEST`;
const GET_SCORES_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SCORES_SUCCESS`;
const GET_ACCORD_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_ACCORD_REQUEST`;
const GET_ACCORD_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_ACCORD_SUCCESS`;
const EXPORT_DATASET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/EXPORT_DATASET_REQUEST`;
const EXPORT_DATASET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/EXPORT_DATASET_SUCCESS`;

// URL getters
const getTaskUrl = id => `${TASKS_URL}${id}/`;
const getExportUrl = id => `${TASKS_URL}${id}/export_supervised_dataset/`;
const getScoreUrl = id => `${TASKS_URL}${id}/expand_evaluation_score/`;
const getAccordUrl = id => `${TASKS_URL}${id}/compute_accord_matrix/`;

// ACTION CREATORS
const getTaskRequest = () => ({ type: GET_TASK_REQUEST });

const getTaskSuccess = data => ({ type: GET_TASK_SUCCESS, data });

const getScoresRequest = taskUuid => ({ type: GET_SCORES_REQUEST, taskUuid });

export const getScoresSuccess = data => ({ type: GET_SCORES_SUCCESS, data });

const getAccordRequest = taskUuid => ({ type: GET_ACCORD_REQUEST, taskUuid });

export const getAccordSuccess = data => ({ type: GET_ACCORD_SUCCESS, data });

const exportDatasetRequest = taskUuid => ({ type: EXPORT_DATASET_REQUEST, taskUuid });

export const exportDatasetSuccess = data => ({ type: EXPORT_DATASET_SUCCESS, data });

export const getTaskFromServer = id => dispatch => {
  dispatch(getTaskRequest());
  return axios
    .get(getTaskUrl(id))
    .then(res => {
      dispatch(getTaskSuccess(res.data))
      return res;
    })
    .catch(handleError);
};

export const getScoresFromServer = (taskUuid, taskId, assignmentId) => dispatch => {
  dispatch(getScoresRequest(taskUuid));
  return axios
    .post(getScoreUrl(taskId), { task_uuid: taskUuid, assignment: assignmentId }) // results will be handled in socket client
    .catch(handleError);
};

export const getAccordFromServer = (taskUuid, taskId) => dispatch => {
  dispatch(getAccordRequest(taskUuid));
  return axios
    .post(getAccordUrl(taskId), { task_uuid: taskUuid }) // results will be handled in socket client
    .catch(handleError);
};

export const exportDataset = (taskUuid, id, name, description, votingThreshold) => dispatch => {
  dispatch(exportDatasetRequest(taskUuid));
  return axios
    .post(getExportUrl(id), { task_uuid: taskUuid, name, description, voting_threshold: votingThreshold }) // results will be handled in socket client
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
  exportTaskUuid: null, // celery (not labeling) task
  getScoresTaskUuid: null,
  getAccordTaskUuid: null,
  task: apiData(Map),
  scores: apiData(List),
  accord: apiData(List),
  exporting: processData(Map)
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_TASK_REQUEST: {
    return state.set('task', Map({
      isLoading: true,
      isError: false,
      data: Map()
    }))
    .set('exporting', processData(Map));
  }

  case GET_TASK_SUCCESS: {
    return state.set('task', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data)
    }));
  }

  case EXPORT_DATASET_REQUEST: {
    return state.set('exporting', Map({
      isLoading: true,
      isError: false,
      isSuccess: false
    }))
    .set('exportTaskUuid', action.taskUuid)
  }

  case EXPORT_DATASET_SUCCESS: {
    return state.set('exporting', Map({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: fromJS(action.data.dataset)
    }))
    .set('task', apiData(Map));
  }

  case GET_SCORES_REQUEST: {
    return state.set('scores', Map({
      isLoading: true,
      isError: false,
      data: List()
    }))
    .set('getScoresTaskUuid', action.taskUuid)
  }

  case GET_SCORES_SUCCESS: {
    return state.set('scores', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data.samples)
    }))
  }

  case GET_ACCORD_REQUEST: {
    return state.set('accord', Map({
      isLoading: true,
      isError: false,
      data: List()
    }))
    .set('getAccordTaskUuid', action.taskUuid)
  }

  case GET_ACCORD_SUCCESS: {
    return state.set('accord', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data.matrix)
    }))
  }

  default: {
    return state
  }
  }
};
