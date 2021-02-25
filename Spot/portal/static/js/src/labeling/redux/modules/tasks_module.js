import axios from 'axios';
import { Map, List, fromJS, toJS } from 'immutable';

// APP CONSTANTS
import { MODULE_NAME } from '../constants';
const CURRENT_NAME = 'tasks_module';

const TASKS_URL = '/api/v1/labeling_task/';
const ASSIGNMENTS_URL = '/api/v1/assignment/';
const DATASETS_URL = '/api/v1/dataset/';

export const EVALUATE_SAMPLES_SIZE = 10;

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const REMOVE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_REQUEST`;
const REMOVE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_SUCCESS`;
const POST_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/POST_REQUEST`;
const POST_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/POST_SUCCESS`;
const ASSIGN_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/ASSIGN_REQUEST`;
const ASSIGN_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/ASSIGN_SUCCESS`;
const UNASSIGN_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/UNASSIGN_REQUEST`;
const UNASSIGN_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/UNASSIGN_SUCCESS`;
const GET_ASSIGNMENTS_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_ASSIGNMENTS_REQUEST`;
const GET_ASSIGNMENTS_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_ASSIGNMENTS_SUCCESS`;
const REJECT_ASSIGNMENT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/REJECT_ASSIGNMENT_REQUEST`;
const REJECT_ASSIGNMENT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/REJECT_ASSIGNMENT_SUCCESS`;
const GET_PREVIEW_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_PREVIEW_REQUEST`;
const GET_PREVIEW_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_PREVIEW_SUCCESS`;
const GET_PREVIEW_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_PREVIEW_ERROR`;
const GET_USERS_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_USERS_REQUEST`;
const GET_USERS_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_USERS_SUCCESS`;
const GET_USERS_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_USERS_ERROR`;
const GET_SAMPLES_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_SAMPLES_REQUEST`;
const GET_SAMPLES_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SAMPLES_SUCCESS`;
const CHANGE_SAMPLE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/CHANGE_SAMPLE_REQUEST`;
const CHANGE_SAMPLE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/CHANGE_SAMPLE_SUCCESS`;
const CHOOSE_DATASET = `${MODULE_NAME}/${CURRENT_NAME}/CHOOSE_DATASET`;
const CHOOSE_ASSIGNEE = `${MODULE_NAME}/${CURRENT_NAME}/CHOOSE_ASSIGNEE`;
const REMOVE_ASSIGNEE = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_ASSIGNEE`;
const RESET_NEW_TASK = `${MODULE_NAME}/${CURRENT_NAME}/RESET_NEW_TASK`;
const SET_LABEL = `${MODULE_NAME}/${CURRENT_NAME}/SET_LABEL`;

// URL getters
const getTaskUrl = id => `${TASKS_URL}${id}/`;
const getAssigmentUrl = id => `${ASSIGNMENTS_URL}${id}/`;
const getPreviewUrl = id => `${DATASETS_URL}${id}/sample/`;
const getUsersUrl = id => `${DATASETS_URL}${id}/allowed_users/`;
const getAssignUrl = id => `${TASKS_URL}${id}/assign/`;
const getUnassignUrl = id => `${TASKS_URL}${id}/unassign/`;
const getSamplesUrl = id => `${DATASETS_URL}${id}/random_sample/`; // test

// ACTION CREATORS
const getRequest = () => ({ type: GET_REQUEST });

const getSuccess = data => ({ type: GET_SUCCESS, data });

const removeRequest = () => ({ type: REMOVE_REQUEST });

const removeSuccess = () => ({ type: REMOVE_SUCCESS });

const postRequest = () => ({ type: POST_REQUEST });

const postSuccess = () => ({ type: POST_SUCCESS });

const assignRequest = () => ({ type: ASSIGN_REQUEST });

const assignSuccess = () => ({ type: ASSIGN_SUCCESS });

const unassignRequest = () => ({ type: UNASSIGN_REQUEST });

const unassignSuccess = () => ({ type: UNASSIGN_SUCCESS });

const getAssignmentsRequest = () => ({ type: GET_ASSIGNMENTS_REQUEST });

const getAssignmentsSuccess = data => ({ type: GET_ASSIGNMENTS_SUCCESS, data });

const rejectAssignmentRequest = () => ({ type: REJECT_ASSIGNMENT_REQUEST });

const rejectAssignmentSuccess = () => ({ type: REJECT_ASSIGNMENT_SUCCESS });

const getPreviewRequest = () => ({ type: GET_PREVIEW_REQUEST });

const getPreviewSuccess = data => ({ type: GET_PREVIEW_SUCCESS, data });

const getPreviewError = err => ({ type: GET_PREVIEW_ERROR, err });

const getUsersRequest = () => ({ type: GET_USERS_REQUEST });

const getUsersSuccess = data => ({ type: GET_USERS_SUCCESS, data });

const getUsersError = err => ({ type: GET_USERS_ERROR, err });

const getSamplesRequest = () => ({ type: GET_SAMPLES_REQUEST });

const getSamplesSuccess = data => ({ type: GET_SAMPLES_SUCCESS, data });

const changeSampleRequest = () => ({ type: CHANGE_SAMPLE_REQUEST });

const changeSampleSuccess = (index, data) => ({ type: CHANGE_SAMPLE_SUCCESS, index, data });

export const chooseDataset = dataset => ({ type: CHOOSE_DATASET, dataset });

export const chooseAssignee = assignee => ({ type: CHOOSE_ASSIGNEE, assignee });

export const removeAssignee = assignee => ({ type: REMOVE_ASSIGNEE, assignee });

export const resetNewTask = () => ({ type: RESET_NEW_TASK });

export const setLabel = (index, label) => ({ type: SET_LABEL, index, label });

export const getFromServer = () => dispatch => {
  dispatch(getRequest());
  return axios
    .get(TASKS_URL)
    .then(res => dispatch(getSuccess(res.data)))
    .catch(handleError);
};

export const removeFromServer = id => dispatch => {
  dispatch(removeRequest());
  return axios
    .delete(getTaskUrl(id))
    .then(res => dispatch(removeSuccess()))
    .catch(handleError);
};

export const postToServer = (datasetId, ownerId, name, description, assigneesIds, samples) => dispatch => {
  dispatch(postRequest());
  return axios
    .post(TASKS_URL, { dataset: datasetId, owner: ownerId, name, description, assignees: assigneesIds, samples })
    .then(res => dispatch(postSuccess()))
    .catch(handleError);
};

export const assignOnServer = (taskId, assigneesIds) => dispatch => {
  dispatch(assignRequest());
  return axios
    .post(getAssignUrl(taskId), { assignees: assigneesIds })
    .then(res => dispatch(assignSuccess()))
    .catch(handleError);
};

export const unassignOnServer = (taskId, assignmentId) => dispatch => {
  dispatch(unassignRequest());
  return axios
    .post(getUnassignUrl(taskId), { assignment: assignmentId })
    .then(res => dispatch(unassignSuccess()))
    .catch(handleError);
};

export const getAssignmentsFromServer = id => dispatch => {
  dispatch(getAssignmentsRequest());
  return axios
    .get(ASSIGNMENTS_URL)
    .then(res => dispatch(getAssignmentsSuccess(res.data)))
    .catch(handleError);
};

export const rejectAssignmentOnServer = id => dispatch => {
  dispatch(rejectAssignmentRequest());
  return axios
    .delete(getAssigmentUrl(id))
    .then(res => dispatch(rejectAssignmentSuccess()))
    .catch(handleError);
};

export const getPreviewFromServer = id => dispatch => {
  dispatch(getPreviewRequest());
  return axios
    .get(getPreviewUrl(id))
    .then(res => dispatch(getPreviewSuccess(res.data)))
    .catch(err => {
      dispatch(getPreviewError(err))
      handleError(err);
    });
};

export const getUsersFromServer = id => dispatch => {
  dispatch(getUsersRequest());
  return axios
    .get(getUsersUrl(id))
    .then(res => dispatch(getUsersSuccess(res.data)))
    .catch(err => {
      dispatch(getUsersError(err));
      handleError(err);
    });
};

export const getSamplesFromServer = id => dispatch => {
  dispatch(getSamplesRequest());
  return axios
    .post(getSamplesUrl(id), { size: EVALUATE_SAMPLES_SIZE, excluded: [] })
    .then(res => dispatch(getSamplesSuccess(res.data.samples)))
    .catch(err => handleError(err));
};

export const changeSampleOnServer = (datasetId, index) => (dispatch, getState) => {
  const excluded = getState().tasksModule.get('samples').get('data').map(x => x.get('index')).toJS();

  dispatch(changeSampleRequest());
  return axios
    .post(getSamplesUrl(datasetId), { size: 1, excluded })
    .then(res => dispatch(changeSampleSuccess(index, res.data.samples[0])))
    .catch(err => handleError(err));
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

// REDUCERS
const initialState = Map({
  tasks: apiData(List),
  assignments: apiData(List),
  preview: apiData(List),
  samples: apiData(List),
  dataset: Map({}),
  assignees: List([])
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_REQUEST: {
    return state.set('tasks', Map({
      isLoading: true,
      isError: false,
      data: List()
    }));
  }

  case GET_SUCCESS: {
    return state.set('tasks', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data)
    }));
  }

  case GET_ASSIGNMENTS_REQUEST: {
    return state.set('assignments', Map({
      isLoading: true,
      isError: false,
      data: List()
    }));
  }

  case GET_ASSIGNMENTS_SUCCESS: {
    return state.set('assignments', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data)
    }));
  }

  case CHOOSE_DATASET: {
    return state.set('dataset', action.dataset);
  }

  case CHOOSE_ASSIGNEE: {
    return state.update('assignees', assignees => {
      // if already assigned
      if(assignees.find(x => x.get('id') === action.assignee.get('id'))) return assignees;

      return assignees.push(action.assignee)
    });
  }

  case REMOVE_ASSIGNEE: {
    return state.update('assignees', assignees => assignees.filter(assignee => assignee.get('id') !== action.assignee.get('id')));
  }

  case RESET_NEW_TASK: {
    return state
      .set('dataset', Map({}))
      .set('assignees', List([]))
      .set('preview', apiData(List))
  }

  case GET_PREVIEW_REQUEST: {
    return state.set('preview', Map({
      isLoading: true,
      isError: false,
      data: List()
    }))
  }

  case GET_PREVIEW_SUCCESS: {
    return state.set('preview', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data.results)
    }))
  }

  case GET_SAMPLES_REQUEST: {
    return state.set('samples', Map({
      isLoading: true,
      isError: false,
      data: List()
    }))
  }

  case GET_SAMPLES_SUCCESS: {
    return state.set('samples', Map({
      isLoading: false,
      isError: false,
      data: fromJS(action.data)
    }))
  }

  case GET_PREVIEW_ERROR: {
    return state.set('preview', Map({
      isLoading: false,
      isError: true,
      data: List()
    }))
  }

  case SET_LABEL: {
    return state.updateIn(['samples', 'data', action.index], sample => sample.set('label', action.label))
  }

  case CHANGE_SAMPLE_SUCCESS: {
    return state.setIn(['samples', 'data', action.index], fromJS(action.data));
  }

  default: {
    return state
  }
  }
};
