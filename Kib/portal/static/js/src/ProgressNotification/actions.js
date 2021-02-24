import { show, hide, removeAll } from 'react-notification-system-redux';
import * as messagesConstants from 'ProgressNotification/constants';

export function triggerProgress(triggered) {
  return dispatch => {
    dispatch({
      type: messagesConstants.TRIGGER_PROGRESS,
      triggered_prog: triggered
    })
  }
}

export function pushLogEntry(entry) {
  return dispatch => {
    dispatch({
      type: messagesConstants.PUSH_LOG,
      entry: entry
    })
  }
}

export function triggerLog(triggered) {
  return dispatch => {
    dispatch({
      type: messagesConstants.TRIGGER_LOG,
      triggered: triggered
    })
  }
}
