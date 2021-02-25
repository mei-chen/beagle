import axios from 'axios';
import { Map, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'user';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_ERROR`;

const URL_DETAILS = '/user_details';

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = (details) => {
  return {
    type: GET_SUCCESS,
    details
  }
};

const getError = () => {
  return {
    type: GET_ERROR
  }
};

// ASYNC ACTION CREATORS
export const getFromServer = () => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(URL_DETAILS)
      .then(response => {
        dispatch(getSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// REDUCERS
const initialState = Map({
    isInitialized: false,
    isLoggedIn: false,
    details: new Map()
});

export default (state=initialState, action={}) => {
  switch (action.type) {

    case GET_SUCCESS: {
      return state.merge({
        isInitialized: true,
        isLoggedIn: !!action.details.username || !!action.details.email,
        details: fromJS(action.details)
      })
    }

    case GET_ERROR: {
      return state.set('isInitialized', true)
    }

    default: {
        return state;
    }
  }
};
