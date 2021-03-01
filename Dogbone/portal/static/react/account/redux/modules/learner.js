import axios from 'axios';
import { Map, List } from 'immutable';
import uuidV4 from 'uuid/v4';

// App
import { MODULE_NAME } from 'common/utils/constants';
import log from 'utils/logging';

// CONSTANTS
const USER_LEARNER_URL = '/api/v1/user/me/learners';
const LEARNER_URL = '/api/v1/ml';
const CURRENT_NAME = 'learner';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const DELETE_LEARNER_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_LEARNER_SUCCESS`;
const RESET_LEARNER_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/RESET_LEARNER_SUCCESS`;
const TOGGLE_ACTIVATE_LEARNER_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/TOGGLE_ACTIVATE_LEARNER_SUCCESS`;
const CHANGE_COLOR_TAG_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CHANGE_COLOR_TAG_SUCCESS`
const CHANGE_COLOR_TAG_FAILED = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CHANGE_COLOR_TAG_FAILED`

// HELPERS
const getLearnerTagUrl = (tag) => `${LEARNER_URL}/${encodeURIComponent(tag)}`;
const getLearnerTagStateUrl = (tag, state) => `${getLearnerTagUrl(tag)}/${state}`;

// ACTION CREATORS
const getSuccess = (learners) => {
  return {
    type: GET_SUCCESS,
    learners
  }
};

const deleteLearnerSuccess = (learner) => {
  return {
    type: DELETE_LEARNER_SUCCESS,
    learner
  }
};

const resetLearnerSuccess = (learner) => {
  return {
    type: RESET_LEARNER_SUCCESS,
    learner
  }
};

const toggleActivateLearnerSuccess = (learner) => {
  return {
    type: TOGGLE_ACTIVATE_LEARNER_SUCCESS,
    learner
  }
};

const changeColorTagSuccess = (learner) => {
  return {
    type: CHANGE_COLOR_TAG_SUCCESS,
    learner
  }
}

const changeColorTagFailed = (learnerName, oldColor) => {
  const learner = {
    name: learnerName,
    color_code: oldColor,

    /*
      sexy trick : triggers the will recive props method in the color picker in case
      the server failed to change it in order to change the color back to previous color
     */
    trigger: uuidV4()
  }

  return {
    type: CHANGE_COLOR_TAG_FAILED,
    learner
  }
}

// Async actions
export const getFromServer = () => {
  return dispatch => {
    return axios.get(USER_LEARNER_URL)
      .then(response => {
        dispatch(getSuccess(response.data.objects))
      }).catch(err => {
        log.error(err.response || err);
      });
  }
};

export const deleteLearner = (tag) => {
  return dispatch => {
    return axios.delete(getLearnerTagUrl(tag))
      .then(response => {
        dispatch(deleteLearnerSuccess(response.data))
      }).catch(err => {
        log.error(err.response || err);
      });
  }
};

export const activateLearner = (tag) => {
  return dispatch => {
    return axios.put(getLearnerTagStateUrl(tag, 'active'))
      .then(response => {
        dispatch(toggleActivateLearnerSuccess(response.data))
      }).catch(err => {
        log.error(err.response || err);
      });
  }
};

export const deactivateLearner = (tag) => {
  return dispatch => {
    return axios.delete(getLearnerTagStateUrl(tag, 'active'))
      .then(response => {
        dispatch(toggleActivateLearnerSuccess(response.data))
      }).catch(err => {
        log.error(err.response || err);
      });
  }
};

export const resetLearner = (tag) => {
  return dispatch => {
    return axios.put(getLearnerTagStateUrl(tag, 'reset'))
      .then(response => {
        dispatch(resetLearnerSuccess(response.data))
      }).catch(err => {
        log.error(err.response || err);
      });
  }
};

export const changeColorTag = (tag,colorCode,oldColor) => {
  return dispatch => {
    return axios.put(getLearnerTagUrl(tag),{ color_code: colorCode })
    .then(response => {
      dispatch(changeColorTagSuccess(response.data))
    }).catch(err => {
      dispatch(changeColorTagFailed(tag,oldColor))
      log.error(err.response || err);
    });
  }
}

// REDUCERS
const initialState = Map({
  isInitialized: false,
  learners: List()
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state;
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      learners: action.learners
    })
  }

  case TOGGLE_ACTIVATE_LEARNER_SUCCESS: {
    return state.update(
      'learners',
      learners => learners.update(
        learners.findIndex(x => x.get('id') === action.learner.id),
        x => x.set('active', action.learner.active)
      )
    )
  }

  case DELETE_LEARNER_SUCCESS: {
    return state.update(
      'learners',
      learners => learners.filter(x => x.get('id') !== action.learner.id)
    );
  }

  case RESET_LEARNER_SUCCESS: {
    return state.update(
      'learners',
      learners => learners.update(
        learners.findIndex(x => x.get('id') === action.learner.id),
        x => x.merge(action.learner)
      )
    )
  }

  case CHANGE_COLOR_TAG_SUCCESS: {
    return state.update(
      'learners',
      learners => learners.update(
        learners.findIndex(x => x.get('id') === action.learner.id),
        x => x.merge(action.learner)
      )
    )
  }

  case CHANGE_COLOR_TAG_FAILED: {
    return state.update(
      'learners',
      learners => learners.update(
        learners.findIndex(x => x.get('name') === action.learner.name),
        x => x.merge(action.learner)
      )
    )
  }

  default: {
    return state
  }
  }
};
