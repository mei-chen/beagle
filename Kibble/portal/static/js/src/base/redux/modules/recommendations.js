import { getFromServer, postToServer, patchToServer, deleteOnServer } from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  POST_ERROR
} from 'base/redux/actions';

const APPLY_ENDPOINT = window.CONFIG.API_URLS.recommendation;

const postRecommendationRequest = () => {
  return {
    type: POST_REQUEST('recommendation')
  };
}


const postRecommendationSuccess = () => {
  return {
    type: POST_SUCCESS('recommendation')
  };
}

const postRecommendationError = () => {
    return {
        type: POST_ERROR('recommendation')
    }
}

export const makeRecommendations = (word, model, successEvent = postRecommendationSuccess,
                           errorEvent = postRecommendationError) => {
  let data = { word: word, model: model.get('api_name')};
  return postToServer({
    endpoint: APPLY_ENDPOINT,
    data,
    processEvent: postRecommendationRequest,
    successEvent,
    errorEvent
  });
};

// REDUCERS
const initialState = [];


export default (state = initialState, action = {}) => {
  switch (action.type) {

    case GET_SUCCESS('recommendation'):
    {
      return action.data;
    }

    default:
    {
      return state;
    }
  }
};
