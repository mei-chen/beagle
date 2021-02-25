import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';
import { REMOVE_SUCCESS } from 'reports-history/redux/modules/history'

// For post requests
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.defaults.xsrfCookieName = 'csrftoken';

const CURRENT_NAME = 'terry';

// ACTION CONSTANTS
const ANALYZE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/ANALYZE_REQUEST`;

const GET_DETAILS_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_DETAILS_REQUEST`;
const GET_DETAILS_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_DETAILS_SUCCESS`;

const GET_RECENT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_RECENT_REQUEST`;
const GET_RECENT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_RECENT_SUCCESS`;

const SET_PACKAGE_MANAGER = `${MODULE_NAME}/${CURRENT_NAME}/SET_PACKAGE_MANAGER`;
const SORT_LICENSES = `${MODULE_NAME}/${CURRENT_NAME}/SORT_LICENSES`;

const URL_BASE = '/api/v1/licenses/';
const REPORT_URL_BASE = '/api/v1/reports/';
const LICENSE_INFO_URL_BASE = '/api/v1/license_details/'

const getAnalizeUrl = key => `${URL_BASE}${key}`;
const getReportUrl = key => `${REPORT_URL_BASE}${key}`;
const getRecentUrl = amount => `${REPORT_URL_BASE}recent/?amount=${amount}`;
const getLicenseInfoUrl = name => `${LICENSE_INFO_URL_BASE}${encodeURIComponent(name)}/`;

// SPECIAL DATA VALUES
export const ERROR = '- FETCH ERROR -';
export const NOT_SPECIFIED = '- NO LICENSE SPECIFIED -';

// ACTION CREATORS
const analyzeRequest = taskUuid => {
  return {
    type: ANALYZE_REQUEST,
    taskUuid
  };
};

const getDetailsRequest = id => {
  return {
    type: GET_DETAILS_REQUEST,
    id
  }
}

const getDetailsSuccess = data => {
  return {
    type: GET_DETAILS_SUCCESS,
    data
  }
}

const getRecentRequest = () => {
  return {
    type: GET_RECENT_REQUEST
  }
}

const getRecentSuccess = data => {
  return {
    type: GET_RECENT_SUCCESS,
    data
  }
}

export const setPackageManager = packageManager => {
  return {
    type: SET_PACKAGE_MANAGER,
    packageManager
  }
}

export const sortLicenses = (columnIndex, direction) => {
  return {
    type: SORT_LICENSES,
    columnIndex,
    direction
  }
}

// ASYNC ACTION CREATORS
export const analyzeProject = (taskUuid, git_url, uuid) => dispatch => {
  dispatch(analyzeRequest(taskUuid));
  return axios.post(getAnalizeUrl('analyze_project/'), { task_uuid: taskUuid, git_url, uuid })
    .catch((err) => {
        console.error(err.response || err);
        throw err;
    });
}

export const getDetailsFromServer = (id, params) => dispatch => {
  dispatch(getDetailsRequest(id));

  return axios.get(getReportUrl(id), { params })
    .then(response => {
      dispatch(getDetailsSuccess(response.data));
    })
    .catch((err) => {
      console.error(err.response || err);
    });
};

export const getRecentFromServer = amount => dispatch => {
  dispatch(getRecentRequest());
  return axios.get(getRecentUrl(amount))
    .then(response => {
      dispatch(getRecentSuccess(response.data));
    })
    .catch((err) => {
      console.error(err.response || err);
    });
};

export const getLicenseInfoServer = name => dispatch => {
  // if multiple licenses in array: send POST
  if(typeof name === 'object') return axios.post(LICENSE_INFO_URL_BASE, { licenses: name });

  return axios.get(getLicenseInfoUrl(name));
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  isNotify: false,
  packageManager: '',
  result: Map(),
  id: null,
  recent: new List(),
  taskUuid: null
});

export default (state=initialState, action={}) => {
  switch (action.type) {


  case ANALYZE_REQUEST: {
    return state.merge({
      isNotify: true,
      taskUuid: action.taskUuid
    })
  }

  case GET_DETAILS_REQUEST: {
    return state.merge({
      isInitialized: false
    })
  }

  case GET_DETAILS_SUCCESS: {
    return state.merge({
      isInitialized: true,
      result: fromJS(action.data.content),
      id: action.data.uuid,
      isNotify: false,
      packageManager: ''
    })
  }

  case GET_RECENT_SUCCESS: {
    return state.set('recent', fromJS(action.data))
  }

  case REMOVE_SUCCESS: {
    return state.set('result', state.get('uuid') === action.id ? state : new Map())
  }

  case SET_PACKAGE_MANAGER: {
    return state.set('packageManager', action.packageManager)
  }

  case SORT_LICENSES: {
    return state.updateIn(['result', 'licenses'], licenses => {
      const sorted = licenses.sortBy(
        // when sorting strings make sort case insensitive
        row => typeof row.get(action.columnIndex) === 'string' ?
          row.get(action.columnIndex).toLowerCase() :
          row.get(action.columnIndex)
      );
      return action.direction === 'asc' ? sorted : sorted.reverse();
    });
  }

  default: {
    return state
  }
  }
};
