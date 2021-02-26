import axios from 'axios';
import { Map, List } from 'immutable';

// App
import { MODULE_NAME } from 'common/utils/constants';
import log from 'utils/logging';
import { Notification } from 'common/redux/modules/transientnotification';

// CONSTANTS
const URL = '/api/v1/keywords';
const CURRENT_NAME = 'keywords';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

const ADD_KEYWORD_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_KEYWORD_SUCCESS`;

const DELETE_KEYWORD_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_KEYWORD_REQUEST`;
const DELETE_KEYWORD_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_KEYWORD_SUCCESS`;

const TOGGLE_ACTIVATE_KEYWORD_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/TOGGLE_ACTIVATE_KEYWORD_SUCCESS`;

// HELPERS
const getKeywordUrl = (keyword) => `${URL}/${encodeURIComponent(keyword)}`;
const getKeywordSubUrl = (keyword, sub) => `${URL}/${keyword}/${sub}`;


// ACTION CREATORS

const getSuccess = (keywords) => {
  return {
    type: GET_SUCCESS,
    keywords
  }
};

const addKeywordSuccess = (keywords) => {
  return {
    type: ADD_KEYWORD_SUCCESS,
    keywords
  }
};

const deleteKeywordRequest = (keyword) => {
  return {
    type: DELETE_KEYWORD_REQUEST,
    keyword
  }
};

const deleteKeywordSuccess = (keyword) => {
  return {
    type: DELETE_KEYWORD_SUCCESS,
    keyword
  }
};

const toggleActivateKeywordSuccess = (keyword) => {
  return {
    type: TOGGLE_ACTIVATE_KEYWORD_SUCCESS,
    keyword
  }
};

// Async actions
export const getFromServer = () => {
  return dispatch => {
    return axios.get(URL)
      .then(response => {
        dispatch(getSuccess(response.data.objects))
      });
  }
};

export const addKeyword = (keyword) => {
  return dispatch => {
    return axios.post(URL, { keyword })
      .then(response => {
        dispatch(addKeywordSuccess(response.data.objects))
      }).catch(err => {
        log.error(err.response || err);
        dispatch(Notification.error(`Add keyword ${keyword} failed.`));
      })
  }
};

export const deleteKeyword = (keyword) => {
  return dispatch => {
    dispatch(deleteKeywordRequest(keyword));
    return axios.delete(getKeywordUrl(keyword))
      .then(response => {
        dispatch(deleteKeywordSuccess(response.data));
      });
  }
};

export const activateKeyword = (keyword) => {
  return dispatch => {
    return axios.post(getKeywordSubUrl(keyword, 'activate'))
      .then(response => {
        dispatch(toggleActivateKeywordSuccess(response.data))
      });
  }
};

export const deactivateKeyword = (keyword) => {
  return dispatch => {
    return axios.post(getKeywordSubUrl(keyword, 'deactivate'))
      .then(response => {
        dispatch(toggleActivateKeywordSuccess(response.data))
      });
  }
};


// REDUCERS
const initialState = Map({
  isInitialized: false,
  keywords: List(),
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state;
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      keywords: action.keywords
    })
  }

  case ADD_KEYWORD_SUCCESS: {
    return state.update('keywords', keywords => keywords.insert(0, Map(action.keywords[0])));
  }

  case DELETE_KEYWORD_SUCCESS: {
    return state.update('keywords', keywords => keywords.filter(x => x.get('keyword') !== action.keyword.keyword));
  }

  case TOGGLE_ACTIVATE_KEYWORD_SUCCESS: {
    return state.update(
      'keywords',
      keywords => keywords.update(
        keywords.findIndex(x => x.get('keyword') === action.keyword.keyword),
        x => x.set('active', action.keyword.active)
      )
    )
  }

  default: {
    return state
  }
  }
};
