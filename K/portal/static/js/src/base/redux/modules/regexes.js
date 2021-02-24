import { getFromServer, postToServer, patchToServer, deleteOnServer } from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  POST_ERROR
} from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.regexList;
const APPLY_ENDPOINT = window.CONFIG.API_URLS.regexApply;

// regexs request
const getRegExRequest = () => {
  return {
    type: GET_REQUEST('regex')
  };
}

const getRegExSuccess = (data) => {
  return {
    type: GET_SUCCESS('regex'),
    data
  };
}

const getRegExError = (err) => {
  return {
    type: GET_ERROR('regex'),
    err
  };
}

const postRegExRequest = () => {
  return {
    type: POST_REQUEST('regex')
  };
}

const postRegExApplyRequest = () => {
  return {
    type: POST_REQUEST('regexApply')
  };
}

const postRegExSuccess = () => {
  return {
    type: POST_SUCCESS('regex')
  };
}

const postRegExApplySuccess = () => {
  return {
    type: POST_SUCCESS('regexApply')
  };
}

const postRegExError = (err) => {
  return {
    type: POST_ERROR('regexApply'),
    err
  };
}

const postRegExApplyError = (err) => {
  return {
    type: POST_ERROR('regexApply'),
    err
  };
}

export const getRegExs = (data = {}) => {
  return getFromServer(
    ENDPOINT, data, getRegExRequest, getRegExSuccess, getRegExError);
}

export const postRegExs = (data, successEvent = postRegExSuccess) => {
  return postToServer({
    endpoint: ENDPOINT,
    data,
    processEvent: postRegExRequest,
    successEvent,
    callbacks: [getRegExs]
  });
}

export const patchRegEx = (endpoint, data, callbacks, successEvent = postRegExSuccess) => {
  return patchToServer({
    endpoint,
    data,
    processEvent: postRegExRequest,
    successEvent,
    callbacks: [getRegExs, ...callbacks]
  });
}

export const deleteRegEx = (endpoint, callbacks, successEvent = postRegExSuccess,
                           errorEvent = postRegExError) => {
  return deleteOnServer({
    endpoint,
    processEvent: postRegExRequest,
    successEvent,
    errorEvent,
    callbacks: [getRegExs, ...callbacks]
  });
}


export const applyRegEx = (regex, batch, successEvent = postRegExApplySuccess,
                           errorEvent = postRegExApplyError) => {
  let data = { batch: batch, regex: regex };
  return postToServer({
    endpoint: APPLY_ENDPOINT,
    data,
    processEvent: postRegExApplyRequest,
    successEvent,
    errorEvent
  });
};

// REDUCERS
const initialState = [];


export default (state = initialState, action = {}) => {
  switch (action.type) {

    case GET_SUCCESS('regex'):
    {
      return action.data;
    }

    default:
    {
      return state;
    }
  }
};
