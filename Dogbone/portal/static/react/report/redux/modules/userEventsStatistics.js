import axios from 'axios';
import log from 'utils/logging';
import { MODULE_NAME } from 'common/utils/constants';

// CONSTANTS
const BASE_URL = '/api/v1/statistics';
const CURRENT_NAME = 'userEventsStatistics';
const SEND_USER_EVENT_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SEND_USER_EVENT_REQUEST`;
const SEND_USER_EVENT_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SEND_USER_EVENT_SUCCESS`;

// ACTIONS
const sendUserEventRequest = () => {
  return {
    type: SEND_USER_EVENT_REQUEST
  }
}

const sendUserEventSuccess = () => {
  return {
    type: SEND_USER_EVENT_SUCCESS
  }
}

export const sendUserEventToServer = (event) => (dispatch) => {
  dispatch(sendUserEventRequest())

  axios
    .post(BASE_URL, { event })
    .then(dispatch(sendUserEventSuccess()))
    .catch((err) => {
      log.error(err.response || err);
      throw err;
    });
}