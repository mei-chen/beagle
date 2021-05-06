import axios from 'axios';
import { Map, List, fromJS } from 'immutable';
import log from 'utils/logging';

// App
import { MODULE_NAME } from 'common/utils/constants';

// CONSTANTS
const CURRENT_NAME = 'experiment';
const EXPERIMENTS_URL = '/api/v1/user/me/spot/experiments';
const SUGGESTIONS_URL = '/api/v1/user/me/spot/suggestions';
const SPOT_AUTHORIZE_URL = '/spot/login';
const KIBBLE_AUTHORIZE_URL = '/kibble/login';
const POST_URL = `${EXPERIMENTS_URL}/add`;
const DELETE_URL = `${EXPERIMENTS_URL}/remove`;
const RESET_URL = `${EXPERIMENTS_URL}/reset`;

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const POST_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/POST_REQUEST`;
const POST_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/POST_SUCCESS`;
const POST_ERROR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/POST_ERROR`;
const DELETE_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_REQUEST`;
const DELETE_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_SUCCESS`;
const RESET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET_REQUEST`;
const RESET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET_SUCCESS`;
const RESET_ERROR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET_ERROR`;
const GET_SUGGESTIONS_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUGGESTIONS_REQUEST`;
const GET_SUGGESTIONS_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUGGESTIONS_SUCCESS`;

// ACTION CREATORS
const getRequest = () => ({ type: GET_REQUEST });

const getSuccess = data => ({ type: GET_SUCCESS, data });

const postRequest = () => ({ type: POST_REQUEST });

const postSuccess = data => ({ type: POST_SUCCESS, data });

const postError = data => ({ type: POST_ERROR, data });

const deleteRequest = () => ({ type: DELETE_REQUEST });

const deleteSuccess = data => ({ type: DELETE_SUCCESS, data });

const resetRequest = () => ({ type: RESET_REQUEST });

const resetSuccess = () => ({ type: RESET_SUCCESS });

const resetError = data => ({ type: RESET_ERROR, data });

const getSuggestionsRequest = () => ({ type: GET_SUGGESTIONS_REQUEST });

const getSuggestionsSuccess = data => ({ type: GET_SUGGESTIONS_SUCCESS, data });

//const spotAuthorizeRequest = () => ({type: SPOT_AUTHORIZE_});

// Async actions
export const getFromServer = () => dispatch => {
  dispatch(getRequest());
  return axios.get(EXPERIMENTS_URL)
    .then(response => {
      dispatch(getSuccess(response.data))
    }).catch(err => {
      log.error(err.response || err);
    });
};

export const postOnServer = uuid => dispatch => {
  dispatch(postRequest());
  return axios.post(POST_URL, { uuid })
    .then(response => {
      dispatch(postSuccess(response.data))
    }).catch(err => {
      const status = err.response.status;
      if (status === 403 || status === 404 || status === 503) dispatch(postError(err.response.data.message))
      log.error(err.response || err);
    });
};

export const deleteFromServer = uuid => dispatch => {
  dispatch(deleteRequest());
  return axios.post(DELETE_URL, { uuid })
    .then(response => {
      dispatch(deleteSuccess(response.data))
    }).catch(err => {
      log.error(err.response || err);
    });
};

export const resetOnServer = uuid => dispatch => {
  dispatch(resetRequest());
  return axios.post(RESET_URL, { uuid })
    .then(response => {
      dispatch(resetSuccess(response.data))
    }).catch(err => {
      // if 404 experiment doesn't exist, disable it
      const { status, data: { message } } = err.response;

      if (status === 404) {
        return dispatch(resetError({ uuid, message }));
      }

      if (status === 403 || status === 503) {
        return dispatch(postError(message));
      }

      log.error(err.response || err);
    });
};

// Don't need to dispatch, nothing to change
export const spotAuthorize = () => {
  return axios.get(SPOT_AUTHORIZE_URL).then(response => {
    // redirect
    let spot_uri = response.data
    window.location.href = spot_uri
  }).catch(err => {
    log.error(err.response || err);
  })
}

export const kibbleAuthorize = () => {
  return axios.get(KIBBLE_AUTHORIZE_URL).then(response => {
    // redirect
    let kibble_uri = response.data
    window.location.href = kibble_uri
  }).catch(err => {
    log.error(err.response || err);
  })
}

export const getSuggetstionsFromServer = () => dispatch => {
  dispatch(getSuggestionsRequest());
  return axios.get(SUGGESTIONS_URL)
    .then(response => {
      dispatch(getSuggestionsSuccess(response.data))
    }).catch(err => {
      log.error(err.response || err);
    });
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  experiments: new Map(),
  suggestions: new List(),
  disabled: new Map(),
  errorMessage: ''
});

export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      experiments: fromJS(action.data)
    })
  }

  case POST_SUCCESS: {
    return state.update('experiments', experiments => experiments.set(action.data.uuid, new Map({ name: action.data.name })))
  }

  case POST_ERROR: {
    return state.set('errorMessage', action.data)
  }

  case DELETE_SUCCESS: {
    return state.update('experiments', experiments => experiments.remove(action.data.uuid))
  }

  case RESET_ERROR: {
    const { uuid, message } = action.data;
    return state.setIn(['disabled', uuid], message);
  }

  case GET_SUGGESTIONS_SUCCESS: {
    return state.set('suggestions', fromJS(action.data))
  }

  default: {
    return state
  }
  }
};
