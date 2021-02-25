import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';

// For post requests
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.defaults.xsrfCookieName = 'csrftoken';

const CURRENT_NAME = 'create_dataset_module';

// ACTION CONSTANTS
const LOAD_DATASET = `${MODULE_NAME}/${CURRENT_NAME}/LOAD_DATASET`;
const CLEAR_DATASET = `${MODULE_NAME}/${CURRENT_NAME}/CLEAR_DATASET`;
const SET_BODY = `${MODULE_NAME}/${CURRENT_NAME}/SET_BODY`;
const SET_LABEL = `${MODULE_NAME}/${CURRENT_NAME}/SET_LABEL`;
const RESET_BODY = `${MODULE_NAME}/${CURRENT_NAME}/RESET_BODY`;
const RESET_LABEL = `${MODULE_NAME}/${CURRENT_NAME}/RESET_LABEL`;
const TOGGLE_HEADER = `${MODULE_NAME}/${CURRENT_NAME}/TOGGLE_HEADER`;
const POST_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/POST_REQUEST`;
const POST_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/POST_SUCCESS`;
const SET_LABEL_STATUS = `${MODULE_NAME}/${CURRENT_NAME}/SET_LABEL_STATUS`;
const RESET_LABEL_STATUS = `${MODULE_NAME}/${CURRENT_NAME}/RESET_LABEL_STATUS`;
const SET_UNMARKED_LABELS_STATUSES = `${MODULE_NAME}/${CURRENT_NAME}/SET_UNMARKED_LABELS_STATUSES`;
const SET_DEFAULT_LABELS_STATUSES = `${MODULE_NAME}/${CURRENT_NAME}/SET_DEFAULT_LABELS_STATUSES`;

// URLS
const URL_BASE = '/api/v1/dataset/'

// ACTION CREATORS
export const loadDataset = (dataset) => {
  return {
    type: LOAD_DATASET,
    dataset
  }
};

export const clearDataset = () => {
  return {
    type: CLEAR_DATASET
  }
}

export const setBody = (index) => {
  return {
    type: SET_BODY,
    index
  }
}

export const setLabel = (index) => {
  return {
    type: SET_LABEL,
    index
  }
}

export const resetBody = () => {
  return {
    type: RESET_BODY
  }
}

export const resetLabel = () => {
  return {
    type: RESET_LABEL
  }
}

export const toggleHeader = status => {
  return {
    type: TOGGLE_HEADER,
    status
  }
}

export const postRequest = () => {
  return {
    type: POST_REQUEST
  }
}

export const postSuccess = data => {
  return {
    type: POST_SUCCESS,
    data
  }
}

export const setLabelStatus = (label, status) => {
  return {
    type: SET_LABEL_STATUS,
    label,
    status
  }
}

export const resetLabelStatus = (label, status) => {
  return {
    type: RESET_LABEL_STATUS,
    label,
    status
  }
}

export const setUnmarkedLabelsStatuses = (status) => {
  return {
    type: SET_UNMARKED_LABELS_STATUSES,
    status
  }
}

export const setDefaultLabelsStatuses = () => {
  return {
    type: SET_DEFAULT_LABELS_STATUSES
  }
}

export const postToServer = (filename, description, data, mapping) => {
  return (dispatch, getState) => {
    dispatch(postRequest());
    return axios.post(URL_BASE, { filename, description, data, mapping })
      .then(response => {
        dispatch(postSuccess(response.data))
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

// HELPERS
const getLabelsList = (dataset, labelColumnIndex) => {
  const allLabels = dataset.map(item => item.get(labelColumnIndex));
  const uniqueLabels = new Set(allLabels);
  return List(uniqueLabels);
}

const removeNotIncluded = (target, source) => {
  return target.filter(el => source.includes(el));
}

const getValue = (list, value) => {
  return list.filter(el => el.toLowerCase() === value.toLowerCase()).get(0);
}

// REDUCERS
const initialState = Map({
  dataset: new List(),
  labels: new List(),
  pos: new List(),
  neg: new List(),
  bodyIndex: null,
  labelIndex: null,
  datasetSaved: false,
  savedDatasetData: Map(),
  isHeaderRemoved: false
});


export default (state=initialState, action={}) => {
  switch (action.type) {
  case LOAD_DATASET: {
    return state.merge({
      dataset: fromJS(action.dataset).map(row => row.map(column => typeof column === 'string' ? column.trim() : column)
      ),
      datasetSaved: false
    })
  }

  case CLEAR_DATASET: {
    return initialState;
  }

  case SET_BODY: {
    return state.set('bodyIndex', action.index);
  }

  case SET_DEFAULT_LABELS_STATUSES: {
    const labels = state.get('labels');
    const trueValue = getValue(labels, 'true');
    const falseValue = getValue(labels, 'false');

    // if the only two labels are "true" and "false" add them to mapping
    if(labels.size === 2 && trueValue && falseValue) {
      return state.set('pos', List([trueValue])).set('neg', List([falseValue]))
    } else {
      return state;
    }
  }

  case SET_LABEL: {
    // if header is removed don't use its label column value in labels list
    const dataset = state.get('isHeaderRemoved') ? state.get('dataset').remove(0) : state.get('dataset');

    return state
      .set('labelIndex', action.index)
      .set('labels', getLabelsList(dataset, action.index))
      .set('pos', new List())
      .set('neg', new List());
  }

  case RESET_BODY: {
    return state.set('bodyIndex', null);
  }

  case RESET_LABEL: {
    return state
      .set('labelIndex', null)
      .set('labels', new List())
      .set('pos', new List())
      .set('neg', new List());
  }

  case TOGGLE_HEADER: {
    let newState = state.set('isHeaderRemoved', action.status);
    const labelColumnIndex = state.get('labelIndex');

    // if user selected label column
    if(labelColumnIndex !== null) {
      // if header is removed don't use its label column value in labels list
      const dataset = action.status ? state.get('dataset').remove(0) : state.get('dataset');
      const labels = getLabelsList(dataset, labelColumnIndex);
      newState = newState.set('labels', labels);

      // if header label was unique and deleted from the list uncheck it
      newState = newState.set('pos', removeNotIncluded(newState.get('pos'), labels));
      newState = newState.set('neg', removeNotIncluded(newState.get('neg'), labels));
    }

    return newState;
  }

  case POST_REQUEST: {
    return state.merge({
      datasetSaving: true,
      datasetSaved: false
    })
  }

  case POST_SUCCESS: {
    return state.merge({
      dataset: new List(),
      bodyIndex: null,
      labelIndex: null,
      datasetSaving: false,
      datasetSaved: true,
      savedDatasetData: fromJS(action.data.dataset)
    })
  }

  case SET_LABEL_STATUS: {
    return state.update(action.status, labels => labels.push(action.label))
  }

  case RESET_LABEL_STATUS: {
    return state.update(action.status, labels => labels.filter(label => label !== action.label));
  }

  case SET_UNMARKED_LABELS_STATUSES: {
    const unmarked = state.get('labels').filter(label => !(state.get('pos').includes(label) || state.get('neg').includes(label)));
    return state.update(action.status, labels => labels.concat(unmarked))
  }

  default: {
    return state
  }
  }
};
