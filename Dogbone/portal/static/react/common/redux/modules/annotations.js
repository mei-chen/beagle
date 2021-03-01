import axios from 'axios';
import { Map } from 'immutable';

import { MODULE_NAME } from 'common/utils/constants';

// CONSTANTS
const CURRENT_NAME = 'annotations';

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
export const getFromServer = (uuid) => {
  return dispatch => {
    const url = `/api/v1/document/${uuid}/annotations`
    dispatch(getRequest());

    return axios.get(url)
      .then(response => {
        dispatch(getSuccess(response.data));
      }).catch(err => {
        dispatch(getError(err)); // Assuming user not logged in
      })
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  annotations:[]
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      annotations:action.data
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