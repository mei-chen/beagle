import axios from 'axios';
import { Map, List } from 'immutable';
import { browserHistory } from 'react-router';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'experiments_module';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const POST_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/POST_REQUEST`;
const POST_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/POST_SUCCESS`;
const POST_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/POST_ERROR`;
const DELETE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_REQUEST`;
const DELETE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_SUCCESS`;
const GET_DEF_NAME_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_DEF_NAME_REQUEST`;
const GET_DEF_NAME_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_DEF_NAME_SUCCESS`;
const RESET_POST_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/RESET_POST_ERROR`;

const URL_BASE = '/api/v1/experiment/';
const URL_DEF_NAME = `${URL_BASE}suggest_default_name`;

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

const postRequest = () => {
  return {
    type: POST_REQUEST
  }
};

const postSuccess = (data) => {
  return {
    type: POST_SUCCESS,
    data
  }
};

const postError = (error) => {
  return {
    type: POST_ERROR,
    error
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

const resetErrorMessage = () => {
  return {
    type: RESET_ERROR_MASSAGE
  }
};

const getDefNameRequest = () => {
  return {
    type: GET_DEF_NAME_REQUEST
  }
};

const getDefNameSuccess = name => {
  return {
    type: GET_DEF_NAME_SUCCESS,
    name
  }
};

export const resetPostError = () => {
  return {
    type: RESET_POST_ERROR
  }
}

// ACTION CREATORS
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

export const postToServer = data => {
  return (dispatch, getState) => {
    dispatch(postRequest())
    return axios.post(URL_BASE, data)
      .then(response => {
        dispatch(postSuccess(response.data));
        if(!response.data.error) browserHistory.push(`/experiments/${response.data.id}/edit`);
      }).catch((err) => {
        if(err.response.status === 400) dispatch(postError(err.response.data.error));
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

export const getDefNameFromServer = () => {
  return (dispatch, getState) => {
    dispatch(getDefNameRequest());
    return axios.get(URL_DEF_NAME)
      .then(response => {
        dispatch(getDefNameSuccess(response.data.next_default_name))
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// HELPERS
export const defaultFormula = [
  {
    weight: 1.0,
    classifier: {
      type: 'trained',
      name: 'Trained Classifier',
      datasets: [],
      model: 'logreg',
      apply: 'include',
      dirty: true,
      training: false,
      scores: null
    }
  }
];


// REDUCERS
const initialState = Map({
  isInitialized: false,
  experiments: new List(),
  postErrorMessage: '',
  defaultName: ''
});


export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      experiments: action.data
    })
  }

  case POST_REQUEST: {
    return state.set('postErrorMessage', '');
  }

  case POST_ERROR: {
    return state.set('postErrorMessage', action.error);
  }

  case DELETE_SUCCESS: {
    return state.update('experiments', experiments => experiments.filter(experiment => {
      return experiment.get('id') !== action.id
    }))
  }

  case GET_DEF_NAME_SUCCESS: {
    return state.set('defaultName', action.name)
  }

  case RESET_POST_ERROR: {
    return state.set('postErrorMessage', '')
  }

  default: {
    return state
  }
  }
};
