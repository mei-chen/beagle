import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'history';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const REMOVE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_REQUEST`;

export const REMOVE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_SUCCESS`;

const URL_BASE = '/api/v1/reports/';
const getReportsUrl = (page, filter) => {
  return filter ? `${URL_BASE}?page=${page}&filter=${filter}` : `${URL_BASE}?page=${page}`;
}

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

const removeRequest = id => {
  return {
    type: REMOVE_REQUEST,
    id
  }
}

const removeSuccess = (id) => {
  return {
    type: REMOVE_SUCCESS,
    id
  }
}

// ASYNC ACTION CREATORS
export const getFromServer = (page, filter) => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(getReportsUrl(page, filter))
      .then(response => {
        dispatch(getSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

export const removeFromServer = id => dispatch => {
  dispatch(removeRequest(id));

  return axios.delete(`${URL_BASE}${id}`)
    .then(response => {
      dispatch(removeSuccess(id));
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};



// REDUCERS
const initialState = Map({
  isInitialized: false,
  reports: new List(),
  pageCount: null
});


export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_REQUEST: {
    return state;
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      reports: action.data.results,
      pageCount: action.data.count
    })
  }

  case REMOVE_SUCCESS: {
    return state.update('reports', reports => reports.filter(report => {
      return report.get('uuid') !== action.id
    }))
  }

  default: {
    return state;
  }
  }
};
