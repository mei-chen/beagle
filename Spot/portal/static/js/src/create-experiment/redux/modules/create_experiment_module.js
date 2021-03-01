import axios from 'axios';
import { Map, List, Set, fromJS, toJS } from 'immutable';
import { browserHistory } from 'react-router';

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'create_experiment_module';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const EDIT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_REQUEST`;
const EDIT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_SUCCESS`;
const EDIT_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_ERROR`;
const ADD_CLASSIFIER = `${MODULE_NAME}/${CURRENT_NAME}/ADD_CLASSIFIER`;
const EDIT_CLASSIFIER = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_CLASSIFIER`;
const REMOVE_CLASSIFIER = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_CLASSIFIER`;
export const DO_HISTORY = `${MODULE_NAME}/${CURRENT_NAME}/DO_HISTORY`;
const UNDO_HISTORY = `${MODULE_NAME}/${CURRENT_NAME}/UNDO_HISTORY`;
const REDO_HISTORY = `${MODULE_NAME}/${CURRENT_NAME}/REDO_HISTORY`;
const RESET_EDIT_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/RESET_EDIT_ERROR`;
const START_TRAINING = `${MODULE_NAME}/${CURRENT_NAME}/START_TRAINING`;
const END_TRAINING = `${MODULE_NAME}/${CURRENT_NAME}/END_TRAINING`;
const QUIT_TRAINING = `${MODULE_NAME}/${CURRENT_NAME}/QUIT_TRAINING`;
const GET_CONFIDENCE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_CONFIDENCE_REQUEST`;
const GET_CONFIDENCE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_CONFIDENCE_SUCCESS`;
const GET_CONFIDENCE_ERROR = `${MODULE_NAME}/${CURRENT_NAME}/GET_CONFIDENCE_ERROR`;

// URLS
const URL_BASE = '/api/v1/experiment/';
const URL_VALIDATE_REGEX = `/api/v1/validate_regex`;
const URL_TRAIN = `/api/v1/train_classifier/`;
const CONFIDENSE_URL = '/api/v1/plot_classifier_decision_function/';

const getConfidenceUrl = uuid => `${CONFIDENSE_URL}${uuid}`;

// ACTION CREATORS
export const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

export const getSuccess = data => {
  return {
    type: GET_SUCCESS,
    data
  }
};

export const editRequest = () => {
  return {
    type: EDIT_REQUEST
  }
};

export const editSuccess = data => {
  return {
    type: EDIT_SUCCESS,
    data
  }
};

export const editError = error => {
  return {
    type: EDIT_ERROR,
    error
  }
};

export const addClassifier = classifier => {
  return {
    type: ADD_CLASSIFIER,
    classifier
  }
};

export const editClassifier = (index, data) => {
  return {
    type: EDIT_CLASSIFIER,
    index,
    data
  }
};

export const removeClassifier = index => {
  return {
    type: REMOVE_CLASSIFIER,
    index
  }
};

export const doHistory = () => {
  return {
    type: DO_HISTORY
  }
};

export const undoHistory = () => {
  return {
    type: UNDO_HISTORY
  }
};

export const redoHistory = () => {
  return {
    type: REDO_HISTORY
  }
};

export const resetEditError = () => {
  return {
    type: RESET_EDIT_ERROR
  }
};

export const startTraining = uuids => {
  return {
    type: START_TRAINING,
    uuids
  }
};

export const endTraining = (uuid, scores) => {
  return {
    type: END_TRAINING,
    uuid,
    scores
  }
}

export const quitTraining = (uuid, errorMessage) => {
  return {
    type: QUIT_TRAINING,
    uuid,
    errorMessage
  }
}

const getConfidenceRequest = uuid => {
  return {
    type: GET_CONFIDENCE_REQUEST,
    uuid
  }
};

export const getConfidenceSuccess = (uuid, confidence) => {
  return {
    type: GET_CONFIDENCE_SUCCESS,
    uuid,
    confidence
  }
};

export const getConfidenceError = (uuid, errorMessage) => {
  return {
    type: GET_CONFIDENCE_ERROR,
    uuid,
    errorMessage
  }
};

// Async actions
export const getFromServer = id => {
  return (dispatch, getState) => {
    dispatch(getRequest());
    return axios.get(`${URL_BASE}${id}/`)
      .then(response => {
        dispatch(getSuccess(response.data))
        dispatch(doHistory())
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
}

export const editOnServer = (id, data) => {
  return (dispatch, getState) => {
    dispatch(editRequest());
    return axios.put(`${URL_BASE}${id}/`, data)
      .then(response => {
        dispatch(editSuccess(response.data));
        dispatch(doHistory())
      }).catch((err) => {
        if(err.response.status === 400) dispatch(editError(err.response.data.error));
        console.error(err.response || err);
        throw err;
      });
  }
};

export const saveCurrentExperimentOnServer = data => {
  // saves current state to server
  // data argument also can be provided
  return (dispatch, getState) => {
    const state = getState().createExperimentModule;
    const id = state.get('id');
    const name = data && data.name || state.get('name');
    const formula = data && data.formula || state.get('formula').toJS();
    return dispatch(editOnServer(id, { name, formula } ))
  }
}

export const validateRegexOnServer = regex => {
  return (dispatch, getState) => {
    return axios.post(URL_VALIDATE_REGEX, { regex });
  }
};

export const trainOnServer = uuids => {
  return (dispatch, getState) => {
    dispatch(startTraining(uuids));
    return axios.post(URL_TRAIN, { uuids });
  };
};

export const getConfidenceFromServer = uuid => {
  return (dispatch, getState) => {
    dispatch(getConfidenceRequest(uuid));
    return axios.get(getConfidenceUrl(uuid)); // response will be handled in socket client
  }
}

// HELPERS
export const defaultClassifier = type => {
  const clf = {
    weight: 0,
    classifier: {
      type,
      apply: 'include'
    }
  }

  if(type === 'regex') {
    clf.classifier.name = 'Regex';
    clf.classifier.expression = '';
  }

  if(type === 'builtin') {
    clf.classifier.name = 'BuiltIn Classifier';
    clf.classifier.model = 'Jurisdiction';
    clf.classifier.description = 'Some description will be here';
    clf.classifier.example = [];
  }

  if(type === 'trained') {
    clf.classifier.name = 'Trained Classifier';
    clf.classifier.model = 'logreg';
    clf.classifier.datasets = [];
    clf.classifier.dirty = true;
    clf.classifier.training = false;
    clf.classifier.decision_threshold = 0;
    clf.classifier.scores = null;
  }

  return clf;
}

// REDUCERS
const initialState = Map({
  id: null,
  uuid: null,
  name: '',
  isOwner: null,
  ownerUsername: null,
  formula: new List(),
  learners: new List(),
  editErrorMessage: '',
  savedFormula: new List(),
  formulaVersions: new List(),
  formulaVersionsHead: 0,
  trainingErrors: new Map(),
  confidenceById: new Map()
});

// REDUCERS
export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_SUCCESS: {
    const formula = fromJS(action.data.formula.content);
    return state.merge({
      id: action.data.id,
      uuid: action.data.uuid,
      name: action.data.name,
      isOwner: action.data.is_owner,
      ownerUsername: action.data.owner_username,
      formula: formula,
      learners: action.data.online_learners,
      savedFormula: formula,
      formulaVersions: new List().unshift(formula),
      formulaVersionsHead: 0
    });
  }

  case EDIT_REQUEST: {
    return state.set('editErrorMessage', '')
  }

  case EDIT_SUCCESS: {
    const formula = fromJS(action.data.formula.content);
    return state.merge({
      id: action.data.id,
      name: action.data.name,
      formula: formula,
      savedFormula: formula
    });
  }

  case EDIT_ERROR: {
    return state.set('editErrorMessage', action.error)
  }

  case ADD_CLASSIFIER: {
    return state.update('formula', formula => formula.push( new fromJS(action.classifier) ))
  }

  case EDIT_CLASSIFIER: {
    let uuid;
    return state
      .update('formula', formula => formula.map((item, i) => {
        if(i === action.index) {
          uuid = item.get('uuid');
          return item.merge(action.data);
        }
        return item;
      }))
      .update('trainingErrors', trainingErrors => trainingErrors.remove(uuid))
  }

  case REMOVE_CLASSIFIER: {
    return state.merge({
      formula: state.get('formula').remove(action.index)
    })
  }

  case DO_HISTORY: {
    const currendHead = state.get('formulaVersionsHead');
    const currentFormula = state.get('formula');
    const currendHeadFormula = state.get('formulaVersions').get(currendHead);

    // if there are no changes: don't do anything
    if( currentFormula.equals(currendHeadFormula) ) return state;

    // if user made UNDO and changed smth: start new HEAD and remove history after this head
    if(currendHead !== 0) {
      return state
        .update('formulaVersions', formulaVersions => formulaVersions.splice(0, currendHead, currentFormula))
        .set('formulaVersionsHead', 0)
    }

    // Default scenario
    return state
        .update('formulaVersions', formulaVersions => formulaVersions.unshift(currentFormula))
        .set('formulaVersionsHead', 0)
  }

  case UNDO_HISTORY: {
    const prevHead = state.get('formulaVersionsHead') + 1;
    const neededFormula = state.get('formulaVersions').get(prevHead);
    return state.merge({
      formula: neededFormula,
      formulaVersionsHead: prevHead
    });
  }

  case REDO_HISTORY: {
    const nextHead = state.get('formulaVersionsHead') - 1;
    const neededFormula = state.get('formulaVersions').get(nextHead);
    return state.merge({
      formula: neededFormula,
      formulaVersionsHead: nextHead
    });
  }

  case RESET_EDIT_ERROR: {
    return state.set('editErrorMessage', '');
  }

  case START_TRAINING: {
    return state
      // set training flags to true
      // reset scores
      .update('formula', formula => formula.map(item => {
        if (action.uuids.indexOf(item.get('uuid')) !== -1) {
            return item.update( 'classifier', clf => clf.merge({ training: true, scores: null }) )
        }
        return item;
      }))
      // reset error messages
      .update('trainingErrors', trainingErrors => {
        let result = trainingErrors;
        trainingErrors.keySeq().forEach(key => {
          if(action.uuids.indexOf(key) !== -1) result = trainingErrors.remove(key);
        });
        return result;
      })
  }

  case END_TRAINING: {
    // set dirty and training flags to false
    return state.update('formula', formula => formula.map(item => {
      if (item.get('uuid') === action.uuid) {
        return item.update( 'classifier', clf => clf.merge({ dirty: false, training: false, scores: action.scores }) )
      }
      return item;
    }))
  }

  case QUIT_TRAINING: {
    return state
      // set training flags to false
      .update('formula', formula => formula.map(item => {
        if (item.get('uuid') === action.uuid) {
          return item.update( 'classifier', clf => clf.set('training', false) )
        }
        return item;
      }))
      // set error message
      .update('trainingErrors', trainingErrors => trainingErrors.set(action.uuid, action.errorMessage))
  }

  case GET_CONFIDENCE_REQUEST: {
    return state.mergeIn(['confidenceById', action.uuid], {
      isLoading: true,
      errorMessage: null,
      data: null
    });
  }

  case GET_CONFIDENCE_SUCCESS: {
    return state.mergeIn(['confidenceById', action.uuid], {
      isLoading: false,
      errorMessage: null,
      data: fromJS(action.confidence)
    });
  }

  case GET_CONFIDENCE_ERROR: {
    return state.mergeIn(['confidenceById', action.uuid], {
      isLoading: false,
      errorMessage: action.errorMessage,
      data: null
    });
  }

  default: {
    return state
  }
  }
};
