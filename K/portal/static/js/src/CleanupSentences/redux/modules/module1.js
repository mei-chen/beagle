import axios from 'axios';
import { Map } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'module1';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

const URL_BASE = '/api/v1/document/';
// const getDocumentByKey = (key) => `${URL_BASE}${key}`;

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  };
};

const getSuccess = (data) => {
  return {
    type: GET_SUCCESS,
    data
  };
};

// Async actions
export const getFromServer = () => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(URL_BASE)
      .then((response) => {
        dispatch(getSuccess(response.data && response.data[0]));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  };
};

// REDUCERS
const initialState = Map({
  isInitialized: false
});


export default (state = initialState, action = {}) => {
  switch (action.type) {
    case GET_REQUEST: {
      return state;
    }

    case GET_SUCCESS: {
      return state.merge({
        isInitialized: true,
        ...action.data,
      });
    }

    default: {
      return state;
    }
  }
};
