import axios from 'axios';
import Cookies from "universal-cookie";
import { SubmissionError } from 'redux-form'


const axiosConf = { headers: { 'Content-Type': 'application/json' } };
const cookies = new Cookies();

export const getFromServer = (endpoint, params, processEvent, successEvent, errorEvent, successExtra) => {
  return (dispatch) => {
    if (processEvent) dispatch(processEvent());
    return axios.get(endpoint, { params })
      .then(response => {
        dispatch(successEvent(response.data, successExtra));
      }).catch((err) => {
        console.error(err.response || err);
        if (errorEvent) {
          dispatch(errorEvent(err.response || err));
        } else {
          throw err;
        }
      });
  }
};

export const postToServer = ({ endpoint, data, processEvent, successEvent, errorEvent, callbacks, headers }) => {
  return (dispatch) => {
    if (processEvent) dispatch(processEvent());
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.post(endpoint, data, Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(successEvent(response.data));
        if (typeof callbacks === 'function') {
          callbacks = [ callbacks ]
        }
        if (Array.isArray(callbacks)) {
          for (const callback of callbacks) {
            dispatch(callback());
          }
        }
      })
      .catch(err => {
        console.error(err.response || err);
        if (errorEvent) {
          dispatch(errorEvent(err.response || err));
        } else {
          throw new SubmissionError(err.response.data);
        }
      });
  }
};

export const patchToServer = ({ endpoint, data, processEvent, successEvent, errorEvent, callbacks, headers }) => {
  return (dispatch) => {
    if (typeof processEvent === 'function') dispatch(processEvent());
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.patch(endpoint, data, Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(successEvent(response.data));
        if (typeof callbacks === 'function') {
          callbacks = [ callbacks ]
        }
        if (Array.isArray(callbacks)) {
          for (const callback of callbacks) {
            dispatch(callback())
          }
        }
      }).catch((err) => {
        console.error(err.response || err);
        if (errorEvent) {
          dispatch(errorEvent(err.response && err.response.statusText || err));
        } else {
          throw new SubmissionError(err.response.data);
        }
      });
  }
};


export const deleteOnServer = ({ endpoint, processEvent, successEvent, errorEvent, callbacks, headers }) => {
  return (dispatch) => {
    if (typeof processEvent === 'function') dispatch(processEvent());
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.delete(endpoint, Object.assign({}, axiosConf, headers))
      .then(response => {
        dispatch(successEvent(response.data));
        if (typeof callbacks === 'function') {
          callbacks = [ callbacks ]
        }
        if (Array.isArray(callbacks)) {
          for (const callback of callbacks) {
            dispatch(callback())
          }
        }
      }).catch((err) => {
        console.error(err.response || err);
        if (errorEvent) {
          dispatch(errorEvent(err.response && err.response.statusText || err));
        } else {
          throw err;
        }
      });
  }
};
