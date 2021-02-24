import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'collaborators_module';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

const INVITE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/INVITE_REQUEST`;
const INVITE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/INVITE_SUCCESS`;
const INVITE_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/INVITE_ERROR`;

const UNINVITE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/UNINVITE_REQUEST`;
const UNINVITE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/UNINVITE_SUCCESS`;

// ENTITY CONSTANTS
export const EXPERIMENT = 'experiment';
export const DATASET = 'dataset';

// URLS
const URL_EXPERIMENT = '/api/v1/experiment/';
const URL_DATASET = '/api/v1/dataset/';
const getBaseUrl = entity => entity === EXPERIMENT ? URL_EXPERIMENT : URL_DATASET;
const getListUrl = (entity, id) => `${getBaseUrl(entity)}${id}/list_collaborators/`;
const getInviteUrl = (entity, id) => `${getBaseUrl(entity)}${id}/invite_collaborator/`;
const getUninviteUrl = (entity, id) => `${getBaseUrl(entity)}${id}/uninvite_collaborator/`;

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = data => {
  return {
    type: GET_SUCCESS,
    data
  }
};

const inviteRequest = () => {
  return {
    type: INVITE_REQUEST
  }
};

const inviteSuccess = () => {
  return {
    type: INVITE_SUCCESS
  }
};

const inviteError = errorMessages => {
  return {
    type: INVITE_ERROR,
    errorMessages
  }
};

const uninviteRequest = () => {
  return {
    type: UNINVITE_REQUEST
  }
};

const uninviteSuccess = () => {
  return {
    type: UNINVITE_SUCCESS
  }
};

export const getFromServer = (entity, id) => {
  return (dispatch, getState) => {
    dispatch(getRequest());
    return axios.get(getListUrl(entity, id))
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

export const inviteOnServer = (entity, id, email) => {
  return (dispatch, getState) => {
    dispatch(inviteRequest());
    return axios.post(getInviteUrl(entity, id), { email })
      .then(response => {
        dispatch(inviteSuccess())
        dispatch(getFromServer(entity, id))
      }).catch((err) => {
        if(err.response.status === 400) dispatch(inviteError(err.response.data));
        console.error(err.response || err);
        throw err;
      });
  }
};

export const uninviteOnServer = (entity, id, username) => {
  return (dispatch, getState) => {
    dispatch(uninviteRequest());
    return axios.post(getUninviteUrl(entity, id), { username })
      .then(response => {
        dispatch(uninviteSuccess())
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// INITIAL STATE
const initialState = Map({
  isInitialized: false,
  collaborators: new List(),
  pendingInvites: new List(),
  inviteErrorMessages: new List()
});

// REDUCERS
export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_REQUEST: {
    return state.set('inviteErrorMessages', new List())
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      collaborators: fromJS(action.data.collaborators),
      pendingInvites: fromJS(action.data.pending_invites)
    })
  }

  case INVITE_REQUEST: {
    return state.set('inviteErrorMessages', new List());
  }

  case INVITE_ERROR: {
    return state.set('inviteErrorMessages', List(action.errorMessages))
  }

  default: {
    return state
  }
  }
};
