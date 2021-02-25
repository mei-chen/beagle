import axios from 'axios';
import Cookies from "universal-cookie";
import { Map } from 'immutable';
import { SubmissionError } from 'redux-form'

import { getFromServer, patchToServer, deleteOnServer, postToServer } from 'base/redux/requests';
import {
    GET_REQUEST,
    GET_SUCCESS,
    GET_ERROR,
    POST_REQUEST,
    POST_SUCCESS,
    POST_ERROR
} from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.keywordListApi;
const SEARCH_ENDPOINT = window.CONFIG.API_URLS.keywordListSearchApi;
const KEYWORD_ENDPOINT = window.CONFIG.API_URLS.keywordApi;

// keywordlists request
const getKeywordListRequest = () => {
  return {
    type: GET_REQUEST('keywordlist')
  };
}

const getKeywordListSuccess = (data, extra) => {
  const type = (extra) ? GET_SUCCESS(extra.type) : GET_SUCCESS('keywordlist');
  const key = (extra) ? extra.key : undefined;
  return {
    type,
    key,
    data
  };
}

const getKeywordListError = (err) => {
  return {
    type: GET_ERROR('keywordlist'),
    err
  };
}

const postKWlistRequest = () => {
  return {
    type: POST_REQUEST('keywordlist')
  };
}

const postKWlistSuccess = (data) => {
  return {
    type: POST_SUCCESS('keywordlist'),
    data
  };
}

const postKWlistError = (err) => {
  return {
    type: POST_ERROR('keywordlist'),
    err
  };
}

const postKeywordRequest = () => {
  return {
    type: POST_REQUEST('keyword')
  };
}

const postKeywordSuccess = (data) => {
  return {
    type: POST_SUCCESS('keyword'),
    data
  };
}

const postKeywordError = (err) => {
  return {
    type: POST_ERROR('keyword'),
    err
  };
}

const postKeywordSearchRequest = () => {
  return {
    type: POST_REQUEST('keywordSearch')
  };
}

const postKeywordSearchSuccess = (data) => {
  return {
    type: POST_SUCCESS('keywordSearch'),
    data
  };
}

const postKeywordSearchError = (err) => {
  return {
    type: POST_ERROR('keywordSearch'),
    err
  };
}


export const getKeywordLists = (data={}, extra) => {
  return getFromServer(
    ENDPOINT, data, getKeywordListRequest, getKeywordListSuccess, getKeywordListError, extra);
}

export const attachKeyword = (data={}) => {
    return postToServer({
      endpoint: KEYWORD_ENDPOINT,
      data,
      processEvent: postKeywordRequest,
      successEvent: postKeywordSuccess
    });
}

export const postKeywordList = (kwlist, origin, keywords, callbacks, successEvent = postKWlistSuccess) => {
  let data = {name: kwlist.name, origin: origin || 'manual', keywords};
  return postToServer({
    endpoint: ENDPOINT,
    data,
    processEvent: postKWlistRequest,
    successEvent,
    callbacks: [getKeywordLists, ...callbacks]
  });
}

export const patchKeywordList = (endpoint, data, callbacks, successEvent = postKWlistSuccess) => {
  return patchToServer({
    endpoint,
    data,
    processEvent: postKWlistRequest,
    successEvent,
    callbacks: [getKeywordLists, ...callbacks]
  });
}

export const deleteKeywordList = (endpoint, callbacks, successEvent = postKWlistSuccess,
                           errorEvent = postKWlistError) => {
  return deleteOnServer({
    endpoint,
    processEvent: postKWlistRequest,
    successEvent,
    errorEvent,
    callbacks: [getKeywordLists, ...callbacks]
  });
}


export const keywordlistSearch = (keywordlist, batch, excludePersonal, successEvent = postKeywordSearchSuccess,
                           errorEvent = postKeywordSearchError) => {
  let data = { batch: batch, keywordlist: keywordlist, obfuscate: excludePersonal};
  return postToServer({
    endpoint: SEARCH_ENDPOINT,
    data,
    processEvent: postKeywordSearchRequest,
    successEvent,
    errorEvent
  });
};

// REDUCERS
const initialState = [];


export default (state=initialState, action={}) => {
  switch (action.type) {

    case GET_SUCCESS('keywordlist'): {
      return action.data;
    }

    default: {
      return state;
    }
  }
};
