import axios from 'axios';
import { Map, List } from 'immutable';
import Cookies from "universal-cookie";

const axiosConf = { headers: { 'Content-Type': 'application/json' } };
const cookies = new Cookies();

// App
import { MODULE_NAME } from '../constants';

const CURRENT_NAME = 'onlineFolder';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_ACCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_ACCESS`;

const URL_BASE = '/api/v1/document/';
const getRequest = () => {
  return {
    type: GET_REQUEST
  };
};

const getAccess = (data) => {
  return {
    type: GET_ACCESS,
    data
  }
};

// Async actions
export const getGoogleDriveAccessLink = () => {
  return dispatch => {
    return axios.get('/api/v1/cloud_auth/set_dropbox_access/')
      .then(response => {
        return response;
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const setDropboxAccess = (token,headers) => {
  return dispatch => {
    dispatch(getRequest());
    const data = {token:token}
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.post('/api/v1/cloud_auth/set_dropbox_access/', data,  Object.assign({}, axiosConf, headers))
      .then(() => {
        dispatch(getAccessInfo());
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
};

export const getAccessInfo = () => {
  return dispatch => {
    dispatch(getRequest());
    return axios.get('/api/v1/cloud_auth/check_access/')
      .then(response => {
        dispatch(getAccess({ cloud_acces_info: response.data }))
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
};

export const getFolders = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get('/api/v1/cloud_folder/')
      .then(response => {
        dispatch(getAccess({ cloud_folders: response.data }))
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
};

export const addCloudFolder = (params,headers) => {
  return dispatch => {
    dispatch(getRequest());
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.post('/api/v1/cloud_folder/', params, Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(getFolders());
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
};

export const revokeDropBoxAccess = (headers) => {
  return dispatch => {
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.delete('/api/v1/cloud_auth/revoke_dropbox_access/',Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(getAccessInfo());
        return response;
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
};

export const revokeGDriveAccess = (headers) => {
  return dispatch => {
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.delete('/api/v1/cloud_auth/revoke_google_drive_access/',Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(getAccessInfo());
        return response;
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
}

export const untrackDropboxFolder = (id,headers) => {
  return dispatch => {
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.delete(`/api/v1/cloud_folder/${id}/`,Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(getFolders());
        return response;
      }).catch((err) => {
        console.log(err.response || err);
        throw err;
      });
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  cloud_acces_info: Map({}),
  cloud_folders: List(),
});


export default (state = initialState, action = {}) => {
  switch (action.type) {
    case GET_REQUEST: {
      return state;
    }

    case GET_ACCESS: {
      return state.merge({
        isInitialized: true,
        ... action.data,
      });
    }


    default: {
      return state;
    }
  }
};
