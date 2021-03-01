import axios from 'axios';
import { Map, List } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'settings';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_ERROR`;
const DELETE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_REQUEST`;
const DELETE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/DELETE_SUCCESS`;

export const GITHUB = 'GITHUB';
export const BITBUCKET = 'BITBUCKET';
export const GITLAB = 'GITLAB';

const getUrl = repoService => {
  switch(repoService) {
    case GITLAB:
      return '/gitlab_token';

    case BITBUCKET:
      return '/bitbucket_token';

    case GITHUB:
    default:
      return '/github_token';
  }
}

const getPropName = repoService => {
  switch(repoService) {
    case GITLAB:
      return 'isGitlabToken';

    case BITBUCKET:
      return 'isBitbucketToken';

    case GITHUB:
    default:
      return 'isGithubToken';
  }
}

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = (repoService, data) => {
  return {
    type: GET_SUCCESS,
    repoService,
    data
  }
};

const getError = () => {
  return {
    type: GET_ERROR
  }
};

const deleteRequest = () => {
  return {
    type: DELETE_REQUEST
  }
};

const deleteSuccess = repoService => {
  return {
    type: DELETE_SUCCESS,
    repoService
  }
};

// ASYNC ACTION CREATORS
export const getFromServer = repoService => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(getUrl(repoService))
      .then(response => {
        dispatch(getSuccess(repoService, response.data));
      }).catch((err) => {
        dispatch(getError())
        console.error(err.response || err);
        throw err;
      });
  }
};

export const deleteFromServer = repoService => {
  return (dispatch) => {
    dispatch(deleteRequest());
    return axios.delete(getUrl(repoService))
      .then(response => {
        dispatch(deleteSuccess(repoService, response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  isGithubToken: false,
  isBitbucketToken: false,
  isGitlabToken: false
});


export default (state=initialState, action={}) => {
  switch (action.type) {
    case GET_SUCCESS: {
      return state.merge({
        isInitialized: true,
        [getPropName(action.repoService)]: action.data.token_exists
      })
    }

    case GET_ERROR: {
      return state.set('isInitialized', true);
    }

    case DELETE_SUCCESS: {
      return state.merge({
        [getPropName(action.repoService)]: false
      })
    }

    default: {
        return state;
    }
  }
};
