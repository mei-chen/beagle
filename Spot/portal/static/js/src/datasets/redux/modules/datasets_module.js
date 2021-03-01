import axios from 'axios';
import { Map, List } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'datasets_module';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const DELETE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_REQUEST`;
const DELETE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_SUCCESS`;

const URL_BASE = '/api/v1/dataset/';
const getDocumentByKey = (key) => `${URL_BASE}${key}`;

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

const deleteRequest = () => {
  return {
    type: DELETE_REQUEST
  }
};

const deleteSuccess = id => {
  return {
    type: DELETE_SUCCESS,
    id
  }
};

// Async actions
export const getFromServer = () => {
  return (dispatch, getState) => {
    dispatch(getRequest());
    return axios.get(URL_BASE)
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

export const deleteFromServer = (id) => {
  return (dispatch, getState) => {
    dispatch(deleteRequest());
    return axios.delete(`${URL_BASE}${id}/`)
      .then(response => {
        dispatch(deleteSuccess(id))
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  datasets: new List()
});


export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      datasets: action.data
    })
  }

  case DELETE_SUCCESS: {
    return state.update('datasets', datasets => datasets.filter(dataset => {
      return dataset.get('id') !== action.id
    }))
  }

  default: {
    return state
  }
  }
};
