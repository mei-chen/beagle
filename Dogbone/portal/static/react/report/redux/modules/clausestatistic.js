import axios from 'axios';
import { Map } from 'immutable';

// App
import log from 'utils/logging';
import { MODULE_NAME } from 'common/utils/constants';


const CURRENT_NAME = 'clausestatistics';

// Async
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

const _getURL = () => '/api/v1/clauses_statistics';

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

export const getFromServer = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get(_getURL())
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

const initialState = Map({
  isInitialized: false,
  isFetching: false
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state.merge({
      isFetching: false
    });
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      isFetching: false,
      ... action.data
    });
  }

  default: {
    return state
  }
  }
}
