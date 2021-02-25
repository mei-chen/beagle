import axios from 'axios';
import { Map, List, fromJS } from 'immutable';

// App
import { MODULE_NAME } from '../constants';
import { getFromServer as getReportsFromServer } from 'reports-history/redux/modules/history'

const CURRENT_NAME = 'permalinks';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const CREATE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/CREATE_REQUEST`;
const CREATE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/CREATE_SUCCESS`;
const REMOVE_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_REQUEST`;
const REMOVE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/REMOVE_SUCCESS`;
const GET_DETAILS_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_DETAILS_REQUEST`;
const GET_DETAILS_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_DETAILS_SUCCESS`;
const EDIT_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_REQUEST`;
const EDIT_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/EDIT_SUCCESS`;

const URL_BASE = '/api/v1/permalinks/';
const getDocumentByKey = key => `${URL_BASE}${key}`;

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = data => {
  return {
    type: GET_SUCCESS,
    data
  }
};

const createRequest = (data) => {
  return {
    type: CREATE_REQUEST,
    data
  }
}

const createSuccess = (data) => {
  return {
    type: CREATE_SUCCESS,
    data
  }
}

const removeRequest = id => {
  return {
    type: REMOVE_REQUEST,
    id
  }
}

const removeSuccess = (id) => {
  return {
    type: REMOVE_SUCCESS,
    id
  }
}

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

const editRequest = () => {
  return {
    type: EDIT_REQUEST
  }
}

const editSuccess = (id, data) => {
  return {
    type: EDIT_SUCCESS
  }
}

// ASYNC ACTION CREATORS
export const getFromServer = () => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(URL_BASE)
      .then(response => {
        dispatch(getSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};

export const create = (data) => dispatch => {
  dispatch(createRequest(data));

  return axios.post(`${URL_BASE}`, data)
    .then(response => {
      dispatch(createSuccess(response));
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const removeFromServer = id => dispatch => {
  dispatch(removeRequest(id));

  return axios.delete(`${URL_BASE}${id}`)
    .then(response => {
      dispatch(removeSuccess(id));
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};

export const getDetailsFromServer = id => dispatch => {
  dispatch(getDetailsRequest(id));

  return axios.get(`${URL_BASE}${id}`)
    .then(response => {
      dispatch(getDetailsSuccess(response.data));
    })
    .catch((err) => {
      console.error(err.response || err);
      throw err;
    });
};


export const editOnServer = (id, name) => {
  return (dispatch) => {
    dispatch(editRequest());
    return axios.put(`${URL_BASE}${id}/`, { name })
      .then(response => {
        dispatch(editSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  }
};


// REDUCERS
const initialState = Map({
  isInitialized: false,
  isCreating: false,
  isRemoving: false,
  reports: new List()
});


export default (state=initialState, action={}) => {
  switch (action.type) {

  case GET_REQUEST: {
    return state;
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      reports: action.data
    })
  }

  case CREATE_REQUEST: {
    return state.merge({
      isCreating: true
    });
  }

  case CREATE_SUCCESS: {
    return state.merge({
      isCreating: false
    })
  }

  case REMOVE_REQUEST: {
    return state.merge({
      isRemoving: true
    });
  }

  case REMOVE_SUCCESS: {
    return state.update('reports', reports => reports.filter(report => {
      return report.get('uuid') !== action.id
    })).merge({
      isRemoving: false
    });
  }

  default: {
    return state;
  }
  }
};
