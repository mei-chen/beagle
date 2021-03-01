import { Map } from 'immutable';
import axios from 'axios';

// App
import { MODULE_NAME } from 'common/utils/constants';

const CURRENT_NAME = 'upload';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

// ASYNC ACTIONS
export const checkForAnalyzed = (batchId) => {
  return () => {
    return axios.get(`/api/v1/batch/${batchId}/check_analysis`)
  }
}

export const sendZipPasswords = (password, upload_id) => {
  return () => {
    return axios.post('/api/v1/upload/set_password_for_zip', { upload_id, password })
  }
}

// REDUCERS
const initialState = Map({
  isInitialized: false
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state;
  }

  case GET_SUCCESS: {
    return state.merge({
      ... action.data
    });
  }

  default: {
    return state
  }
  }
};
