import axios from 'axios';
import { Map } from 'immutable';

import { GET_REQUEST, GET_SUCCESS, GET_ERROR, INIT_UI } from 'base/redux/actions';
import { getFromServer } from 'base/redux/requests';

const URL_DETAILS = '/user_details';


// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST('user')
  }
};

const getSuccess = (data) => {
  return {
    type: GET_SUCCESS('user'),
    data
  }
};

export const getLoggedUser = () => {
  return getFromServer(
    URL_DETAILS, {}, getRequest, getSuccess);
}

// REDUCERS
const initialState = Map({
    isInitialized: false,
    isLoggedIn: false,
    details: new Map()
});


export default (state=initialState, action={}) => {
  switch (action.type) {

    case GET_SUCCESS('user'): {
      return state.merge({
        isInitialized: true,
        isLoggedIn: true,
        details: Map(action.data)
      })
    }

    default: {
        return state;
    }
  }
};
