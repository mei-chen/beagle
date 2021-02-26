import uuidV4 from 'uuid/v4';
import { Map, List } from 'immutable';

import { MODULE_NAME } from 'common/utils/constants';

// CONSTANTS
const CURRENT_NAME = 'transientnotification';

// ACTION CONSTANTS
const ADD_NOTIFICATION = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_NOTIFICATION`;
const REMOVE_NOTIFICATION = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/REMOVE_NOTIFICATION`;

const addNotification = (msg, url, _type, style, key) => {
  return {
    type: ADD_NOTIFICATION,
    msg,
    url,
    _type,  // Prevent conflict with redux dispatch type
    style,
    key
  }
};

export const Notification = {
  error(msg, url, key) {
    return this.toastError(msg, url, key);
  },

  info(msg, url, key) {
    return this.toastInfo(msg, url, key);
  },

  success(msg, url, key) {
    return this.toastSuccess(msg, url, key);
  },

  toastError(msg, url, key) {
    return addNotification(msg, url, 'error', 'toast', key);
  },

  toastInfo(msg, url, key) {
    return addNotification(msg, url, 'info', 'toast', key);
  },

  toastSuccess(msg, url, key) {
    return addNotification(msg, url, 'success', 'toast', key);
  },

  croutonError(msg, url) {
    return addNotification(msg, url, 'error', 'crouton');
  },

  croutonInfo(msg, url) {
    return addNotification(msg, url, 'info', 'crouton');
  },

  croutonSuccess(msg, url) {
    return addNotification(msg, url, 'success', 'crouton');
  }
};

export const removeNotification = (uuid) => {
  return {
    type: REMOVE_NOTIFICATION,
    uuid
  }
};

// REDUCERS
const initialState = Map({
  notifications: List()
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case ADD_NOTIFICATION: {
/*
    check if a notification with the same key is already displayed
    socketListener method is found usualy in componentDidMount witch sometimes is trigerd more times
    pushing more times same notification
*/
    let key = action.key;
    if (key && state.get('notifications').find(notif => notif.get('key') === key)) {
      return state;
    }

    let new_notif = Map({
      uuid: uuidV4(),
      msg: action.msg,
      url: action.url,
      style: action.style,
      type: action._type,
      key: action.key
    });
    return state.update(
      'notifications',
      notifications => notifications.push(new_notif)
    );
  }

  case REMOVE_NOTIFICATION: {
    return state.update(
      'notifications',
      notifications => notifications.filter(x => x.get('uuid') !== action.uuid)
    );
  }

  default: {
    return state
  }
  }
};
