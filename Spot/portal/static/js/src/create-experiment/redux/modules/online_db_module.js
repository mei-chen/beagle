import axios from 'axios';
import { Map, List, Set, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'online_db_module';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const POST_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/POST_REQUEST`;
const POST_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/POST_SUCCESS`;
const EDIT_SAMPLE = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_SAMPLE`;
const REMOVE_SAMPLE = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_SAMPLE`;
const COLLECT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/COLLECT_REQUEST`;
const COLLECT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/COLLECT_SUCCESS`;
const RESET_COLLECT = `${MODULE_NAME}/${CURRENT_NAME}/RESET_COLLECT`;

// OTHER CONST
export const TAGGED = 'tagged';
export const INFERRED = 'inferred';

// URLS
const getSamplesUrl = uuid => `/api/v1/publish/${uuid}/get_samples/`;
const getUpdateUrl = uuid => `/api/v1/publish/${uuid}/update_samples/`;
const getCollectUrl = uuid => `/api/v1/publish/${uuid}/collect_to_dataset/`;

// ACTION CREATORS
const getRequest = () => ({ type: GET_REQUEST });

const getSuccess = data => ({ type: GET_SUCCESS, data });

const postRequest = () => ({ type: POST_REQUEST });

const postSuccess = data => ({ type: POST_SUCCESS, data });

export const editSample = (category, index, data) => ({ type: EDIT_SAMPLE, category, index, data });

export const removeSample = (category, index) => ({ type: REMOVE_SAMPLE, category, index });

const collectRequest = () => ({ type: COLLECT_REQUEST });

const collectSuccess = data => ({ type: COLLECT_SUCCESS, data });

export const resetCollect = data => ({ type: RESET_COLLECT, data });

export const getFromServer = (uuid, tag) => dispatch => {
  dispatch(getRequest())
  return axios.post(getSamplesUrl(uuid), { tag })
    .then(res => {
      dispatch(getSuccess(res.data))
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const postToServer = (uuid, data) => (dispatch, getState) => {
  dispatch(postRequest())
  return axios.post(getUpdateUrl(uuid), data)
    .then(res => {
      dispatch(postSuccess(res.data))
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const collectOnServer = (uuid, tag, name, includeInferred) => (dispatch, getState) => {
  dispatch(collectRequest())
  return axios.post(getCollectUrl(uuid), { tag, name, include_inferred: includeInferred })
    .then(res => {
      dispatch(collectSuccess(res.data))
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

// INITIAL STATE
const initialState = Map({
  [TAGGED]: new Map(),
  [INFERRED]: new Map(),
  updates: new Map({
    add: new Map(),
    edit: new Map(),
    remove: new Set()
  }),
  collecting: new Map({
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: new Map()
  })
});

// HELPERS
const listToMap = list => list.reduce((map, sample) => map = map.set(sample.get('index'), sample), Map());

export const mapToList = map => map.valueSeq();

// REDUCERS
export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_SUCCESS: {
    const { tagged, inferred } = action.data;

    return state.merge({
      [TAGGED]: listToMap( fromJS(tagged) ),
      [INFERRED]: listToMap( fromJS(inferred) )
    });
  }

  case EDIT_SAMPLE: {
    return state
      .updateIn([action.category, action.index], sample => sample.merge(action.data))
      .updateIn(['updates', 'edit', action.index], sample => {
        if(!sample) return new Map(action.data);
        return sample.merge(action.data);
      })
  }

  case REMOVE_SAMPLE: {
    return state
      .deleteIn([action.category, action.index])
      .updateIn(['updates', 'remove'], indexes => indexes.add(action.index))
      .deleteIn(['updates', 'edit', action.index])
      .deleteIn(['updates', 'add', action.index]);
  }

  case COLLECT_REQUEST: {
    return state.set('collecting', Map({
      isLoading: true,
      isError: false,
      isSuccess: false,
      data: new Map()
    }))
  }

  case COLLECT_SUCCESS: {
    return state.set('collecting', Map({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: fromJS(action.data.dataset)
    }))
  }

  case RESET_COLLECT: {
    return state.set('collecting', Map({
      isLoading: false,
      isError: false,
      isSuccess: false,
      data: new Map()
    }))
  }

  default: {
    return state
  }
  }
};
