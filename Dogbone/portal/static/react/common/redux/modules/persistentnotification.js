import axios from 'axios';
import { Map, List } from 'immutable';

import log from 'utils/logging';
import { Notification } from 'common/redux/modules/transientnotification';
import { MODULE_NAME } from 'common/utils/constants';

// URLS
const URL = '/api/v1/user/me/inbox';
const CURRENT_NAME = 'persistentnotification';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

const MARK_READ_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/MARK_READ_REQUEST`;
const MARK_READ_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/MARK_READ_SUCCESS`;

const MARK_ALL_READ_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/MARK_ALL_READ_REQUEST`;
const MARK_ALL_READ_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/MARK_ALL_READ_SUCCESS`;

const APPEND_TO_NOTIFS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/APPEND_TO_NOTIFS`;
const UPDATE_PAGE_NUMBER = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/UPDATE_PAGE_NUMBER`;

const RESET = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET`;

// HELPERS
const getUrl = (page=0) => `${URL}?rpp=5&page=${page}`;


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

const markReadRequest = () => {
  return {
    type: MARK_READ_REQUEST
  }
};

const markReadSuccess = (data) => {
  return {
    type: MARK_READ_SUCCESS,
    data
  }
};

const markAllReadRequest = () => {
  return {
    type: MARK_ALL_READ_REQUEST
  }
};

const markAllReadSuccess = (data) => {
  return {
    type: MARK_ALL_READ_SUCCESS,
    data
  }
};

export const reset = () => {
  return {
    type: RESET
  }
};

export const appendToNotifs = (notif) => {
  return {
    type: APPEND_TO_NOTIFS,
    notif
  }
}

export const updatePageNumber = (page) => {
  return {
    type: UPDATE_PAGE_NUMBER,
    page
  }
}

// Async actions
export const getFromServer = () => {
  return (dispatch, getState) => {
    dispatch(getRequest());

    const state = getState();
    const page = state.persistentnotification.get('page')

    return axios.get(getUrl(page))
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch(err => {
        log.error('get notifications error', err.response || err);
        dispatch(Notification.error('Failed to update notification inbox.'));
      })
  }
};

export const markRead = (id) => {
  return dispatch => {
    dispatch(markReadRequest());

    return axios.put(`${URL}/${id}`, { read: true })
      .then(resp => {
        dispatch(markAllReadSuccess(resp.data))
      }).catch(err => {
        log.error('mark read failed', err.response || err);
        dispatch(Notification.error('Mark notification as read failed.'));
      })
  }
}

export const markAllRead = () => {
  return dispatch => {
    dispatch(markAllReadRequest());

    return axios.post(`${URL}/mark_all`, { read: true })
      .then(resp => {
        dispatch(markAllReadSuccess());

        for (let obj in resp.data.objects) {
          log(resp.data, obj);
          dispatch(markReadSuccess(obj));
        }
        dispatch(getFromServer());
      }).catch(resp => {
        log.error('failed to mark notifications as read', resp);
        dispatch(Notification.error('Failed to mark all as read.'));
      })
  }
}

// REDUCERS
const initialState = Map({
  isLoading: false,
  isInitialized: false,
  objects: List(),
  meta: Map({}),
  page: 0,
  didGetData: false
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case RESET: {
    return state.merge({
      objects: List(),
      page: 0
    });
  }

  case GET_REQUEST: {
    return state.merge({
      isLoading: true
    });
  }

  case GET_SUCCESS: {
    return state.merge({
      isLoading: false,
      isInitialized: true,
      meta: action.data.meta,
    }).update(
      'objects',
      objects => objects
        .concat(action.data.objects.map(x => Map(x)))
        .sortBy(x => x.get('id'))
        .reverse()
    )
  }

  case APPEND_TO_NOTIFS: {
    return state.update(
      'objects',
      objects => objects
        .push(Map(action.notif))
        .sortBy(x => x.get('id'))
        .reverse()
    );
  }

  case UPDATE_PAGE_NUMBER: {
    return state.merge({
      page: action.page
    })
  }

  case MARK_READ_SUCCESS: {
    return state.update(
      'objects',
      objects => objects.update(
        objects.findIndex(x => x.get('id') === action.data.id),
        x => x.merge(action.data)
      )
    )
  }

  case MARK_ALL_READ_SUCCESS: {
    return state;
  }

  default: {
    return state
  }
  }
};
