import { Map, List } from 'immutable';
import axios from 'axios';

import { Notification } from 'common/redux/modules/transientnotification';
import { MODULE_NAME } from 'common/utils/constants';
import log from 'utils/logging';
// CONSTANTS
const URL = '/api/v1/user/me';
const CURRENT_NAME = 'user';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_ERROR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_ERROR`;
const UPDATE_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/UPDATE_SUCCESS`;

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = (data) => {
  return {
    type: GET_SUCCESS,
    data
  }
};

const getError = () => {
  return {
    type: GET_ERROR
  }
};

const updateSuccess = (data) => {
  return {
    type: UPDATE_SUCCESS,
    data
  }
};

// Async actions
export const getFromServer = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get(URL)
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch(err => {
        dispatch(getError(err)); // Assuming user not logged in
      });
  }
};

export const updateProfileData = (data) => {
  return dispatch => {
    return axios.put('/api/v1/user/me',data)
      .then(response => {
        dispatch(updateSuccess(response.data));
        dispatch(Notification.success('Profile Updated'));
        return response.data;
      }).catch(err => {
        log.error(err.response || err);
        dispatch(Notification.error('Profile Update Failed'));
      });
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  first_name: undefined,
  last_name: undefined,
  username: undefined,
  avatar: undefined,
  company: undefined,
  date_joined: undefined,
  document_upload_count: undefined,
  email: undefined,
  had_trial: undefined,
  id: undefined,
  is_super: undefined,
  job_title: undefined,
  keywords: undefined,
  last_login: undefined,
  pending: undefined,
  phone: undefined,
  settings: Map({}),
  tags: List(),
  token: undefined,
  token_expire: undefined,
  is_paid: undefined
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state;
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      ... action.data
    })
  }

  case GET_ERROR: {
    return state.merge({
      isInitialized: true,
    })
  }

  case UPDATE_SUCCESS: {
    return state.merge({
      ... action.data
    });
  }

  default: {
    return state
  }
  }
};
