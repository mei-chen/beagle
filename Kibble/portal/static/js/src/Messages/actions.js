import { show, hide, removeAll } from 'react-notification-system-redux';
import * as messagesConstants from 'Messages/constants';


const opts = {
  position: 'br',
  autoDismiss: 0,
  title: ' '
}

export function pushMessage(message, level) {
  const msg = {
    ...opts,
    message: message,
    uid: Date.now(),
  }

  return dispatch => dispatch({
    type: messagesConstants.PUSH_MESSAGE,
    level: level,
    message: msg,
  })
}

export function showNotification(message, level) {
  return dispatch => {
    dispatch({
      type: messagesConstants.DISMISS_MESSAGE,
      uid: message.uid,
    });
    dispatch(show(message, level));
  }
}

export function clearMessages() {
  return dispatch => {
    dispatch(removeAll());
    dispatch({
      type: messagesConstants.CLEAR_MESSAGES,
    })
  }
}

export function dismissMessage(uid) {
  return dispatch => {
    dispatch(hide(uid));
    dispatch({
      type: messagesConstants.DISMISS_MESSAGE,
      uid
    })

  }
}
