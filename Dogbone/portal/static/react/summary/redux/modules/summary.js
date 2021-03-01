import axios from 'axios';
import { Map, List } from 'immutable';

//App
import { MODULE_NAME } from 'common/utils/constants';
import log from 'utils/logging';

// CONSTANTS
const CURRENT_NAME = 'summary';

// Current Batch
const node = document.getElementById('_id');
const batchID = node != null ? node.value : null;

// ACTION CONSTANTS
// Sync
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;

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

// Async actions
export const getFromServer = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get(`details/${batchID}`)
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  isFetching: false,
  analyzed: null,
  batch_id: null,
  upload_title: null,
  documents_count: null,
  created: null,
  documents: List(),
  docstats: Map({}),
})

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state.merge({
      isFetching: false
    });
  }
  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      isFetching: false,
      batch_id: batchID,
      ... action.data
    });
  }
  default: {
    return state;
  }
  }
}
