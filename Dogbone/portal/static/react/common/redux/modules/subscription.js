import axios from 'axios';
import { Map } from 'immutable';

import { MODULE_NAME } from 'common/utils/constants';

// CONSTANTS
const URL = '/api/v1/user/me/subscription';
const CURRENT_NAME = 'subscription';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_ERROR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_ERROR`;

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

// Async actions
export const getFromServer = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get(URL)
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch(err => {
        dispatch(getError(err)); // Assuming user not logged in
      })
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state
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

  default: {
    return state
  }
  }
};
