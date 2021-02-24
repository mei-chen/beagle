import { getFromServer, postToServer, patchToServer, deleteOnServer } from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  POST_ERROR
} from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.synonyms;

const postSynonymsRequest = () => {
  return {
    type: POST_REQUEST('synonyms')
  };
}

const postSynonymsSuccess = () => {
  return {
    type: POST_SUCCESS('synonyms')
  };
}

const postSynonymsError = () => {
  return {
    type: POST_ERROR('synonyms')
  };
}

export const getSynonyms = (word, successEvent = postSynonymsSuccess, errorEvent = postSynonymsError) => {
  const data = { word: word };
  return postToServer({
    endpoint: ENDPOINT,
    data,
    processEvent: postSynonymsRequest,
    successEvent,
    errorEvent
  });
};

// REDUCERS
const initialState = [];


export default (state = initialState, action = {}) => {
  switch (action.type) {

    case GET_SUCCESS('synonyms'):
    {
      return action.data;
    }

    default:
    {
      return state;
    }
  }
};
