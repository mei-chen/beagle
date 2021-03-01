import { getFromServer, postToServer, patchToServer, deleteOnServer } from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  POST_ERROR
} from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.sentences;

const postSentencesRequest = () => {
  return {
    type: POST_REQUEST('sentences')
  };
}

const postSentencesSuccess = () => {
  return {
    type: POST_SUCCESS('sentences')
  };
}

const postSentencesError = () => {
  return {
    type: POST_ERROR('sentences')
  };
}

export const getSentences = (data, successEvent = postSentencesSuccess, errorEvent = postSentencesError) => {
  return postToServer({
    endpoint: ENDPOINT,
    data,
    processEvent: postSentencesRequest,
    successEvent,
    errorEvent
  });
};

// REDUCERS
const initialState = [];


export default (state = initialState, action = {}) => {
  switch (action.type) {

    case GET_SUCCESS('sentences'):
    {
      return action.data;
    }

    default:
    {
      return state;
    }
  }
};
