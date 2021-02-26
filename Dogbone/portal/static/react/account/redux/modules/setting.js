import axios from 'axios';
import { Map, List } from 'immutable';
import log from 'utils/logging';

import { MODULE_NAME } from 'common/utils/constants';

// CONSTANTS
const URL = '/api/v1/user/me/settings';
const ANALYSIS_OPTIONS_URL = '/api/v1/user/me/rlte_flags';
const CURRENT_NAME = 'settings';

const DEFAULT_SETTINGS = {
  finished_processing_notification: true,
  collaboration_invite_notification: true,
  comment_mention_notification: true,
  owner_changed_notification: true,
  email_digest_notification: true,
  include_clause_in_outcoming_mention_emails: true,
  default_report_view: '#/widget-panel'
}

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_ACCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_ACCESS`;
const DROPBOX_REQUEST_STARTED = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DROPBOX_REQUEST_STARTED`;
const DROPBOX_REQUEST_FINISHED = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DROPBOX_REQUEST_FINISHED`;
const GDRIVE_REQUEST_STARTED = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GDRIVE_REQUEST_STARTED`;
const GDRIVE_REQUEST_FINISHED = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GDRIVE_REQUEST_FINISHED`;
const UPDATE_SETTING_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/UPDATE_SETTING_SUCCESS`;
const GET_ANALYSIS_OPTIONS_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_ANALYSIS_OPTIONS_REQUEST`;
const GET_ANALYSIS_OPTIONS_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_ANALYSIS_OPTIONS_SUCCESS`;
const TOGGLE_ANALYSIS_OPTIONS_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/TOGGLE_ANALYSIS_OPTIONS_REQUEST`;
const TOGGLE_ANALYSIS_OPTIONS_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/TOGGLE_ANALYSIS_OPTIONS_SUCCESS`;


const xand4 = function(a, b, c, d) {
  return ((a == b) && (b == c) && (c == d));
}

// Helpers
const isSameState = (settings) => {
  const {
    finished_processing_notification,
    collaboration_invite_notification,
    comment_mention_notification,
    owner_changed_notification
  } = settings;

  return xand4(
    finished_processing_notification,
    collaboration_invite_notification,
    comment_mention_notification,
    owner_changed_notification
  );
}

// ACTION CREATORS
const getRequest = () => {
  return {
    type: GET_REQUEST
  }
};

const getSuccess = (data) => {
  return {
    type: GET_SUCCESS,
    data
  }
};

const getAccess = (data) => {
  return {
    type: GET_ACCESS,
    data
  }
};

const updateSettingSuccess = (data) => {
  return {
    type: UPDATE_SETTING_SUCCESS,
    data
  }
};

const dropboxRequestStarted = () => {
  return {
    type: DROPBOX_REQUEST_STARTED
  }
}

const dropboxRequestFinished = () => {
  return {
    type: DROPBOX_REQUEST_FINISHED
  }
}

const gdriveRequestStarted = () => {
  return {
    type: GDRIVE_REQUEST_STARTED
  }
}

const gdriveRequestFinished = () => {
  return {
    type: GDRIVE_REQUEST_FINISHED
  }
}

const toggleAnalysisOptionRequest = () => {
  return {
    type: TOGGLE_ANALYSIS_OPTIONS_REQUEST
  }
}

const toggleAnalysisOptionSuccess = (option, active) => {
  return {
    type: TOGGLE_ANALYSIS_OPTIONS_SUCCESS,
    option,
    active
  }
}

const getAnalysisOptionRequest = () => {
  return {
    type: GET_ANALYSIS_OPTIONS_REQUEST
  }
}

const getAnalysisOptionSuccess = data => {
  return {
    type: GET_ANALYSIS_OPTIONS_SUCCESS,
    data
  }
}

// Async actions
export const getFromServer = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get(URL)
      .then(response => {
        // if response object is empty (if settings page first accessed)
        // set default settings
        if (Object.keys(response.data).length === 0) {
          dispatch(updateSettings(DEFAULT_SETTINGS))
        } else {
          dispatch(getSuccess(response.data))
        }

        dispatch(getFolders());
        dispatch(getAccessInfo());
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const getFolders = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get('/api/v1/upload/get_cloud_folders')
      .then(response => {
        dispatch(getAccess({ cloud_folders: response.data }))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const setDropboxAccess = (token) => {
  return dispatch => {
    dispatch(getRequest());

    return axios.post('/api/v1/upload/set_dropbox_token', { token })
      .then(() => {
        dispatch(getAccessInfo());
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const getAccessInfo = () => {
  return dispatch => {
    dispatch(getRequest());

    return axios.get('/api/v1/upload/get_cloud_access')
      .then(response => {
        dispatch(getAccess({ cloud_acces_info: response.data }))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const updateSettings = (data) => {
  return dispatch => {
    return axios.put(URL, data)
      .then(response => {
        dispatch(updateSettingSuccess(response.data))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const getGoogleDriveAccessLink = () => {
  return dispatch => {
    dispatch(gdriveRequestStarted())
    return axios.get('/api/v1/upload/set_google_drive_secret')
      .then(response => {
        dispatch(gdriveRequestFinished());
        return response;
      }).catch((err) => {
        dispatch(gdriveRequestFinished());
        log.error(err.response || err);
        throw err;
      });
  }
};

export const addCloudFolder = (params) => {
  return dispatch => {
    dispatch(dropboxRequestStarted())
    return axios.post('/api/v1/upload/add_cloud_folder', params)
      .then(response => {
        dispatch(dropboxRequestFinished());
        return response;
      }).catch((err) => {
        dispatch(dropboxRequestFinished());
        log.error(err.response || err);
        throw err;
      });
  }
};

export const revokeGoogleDriveAccess = () => {
  return dispatch => {
    return axios.get('/api/v1/upload/revoke_google_drive_access')
      .then(response => {
        dispatch(getAccessInfo());
        return response;
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const revokeDropBoxAccess = () => {
  return dispatch => {
    return axios.get('/api/v1/upload/revoke_dropbox_access')
      .then(response => {
        dispatch(getAccessInfo());
        return response;
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const getAnalysisOptions = () => {
  return dispatch => {
    dispatch(getAnalysisOptionRequest());
    return axios.get(ANALYSIS_OPTIONS_URL)
      .then(resp => {
        dispatch(getAnalysisOptionSuccess(resp.data))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

export const toggleAnalysisOption = (option, active) => {
  return dispatch => {
    dispatch(toggleAnalysisOptionRequest());
    return axios.put(ANALYSIS_OPTIONS_URL, { [option]: active })
      .then(() => {
        dispatch(toggleAnalysisOptionSuccess(option, active))
      }).catch((err) => {
        log.error(err.response || err);
        throw err;
      });
  }
};

// REDUCERS
const initialState = Map({
  isInitialized: false,
  dropboxIsLoading: false,
  googleDriveIsLoading: false,
  finished_processing_notification: null,
  collaboration_invite_notification: null,
  comment_mention_notification: null,
  owner_changed_notification: null,
  email_digest_notification: null,
  include_clause_in_outcoming_mention_emails: null,
  default_report_view: null,
  show_learner_help_text: null,
  email_notification_customized: null,
  email_notification_active: null,
  analysis_options: Map({}),
  onlineFolderWatcher: null,
  cloud_folders: List(),
  cloud_acces_info: Map({}),
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case GET_REQUEST: {
    return state;
  }

  case DROPBOX_REQUEST_STARTED: {
    return state
      .set('dropboxIsLoading', true);
  }

  case DROPBOX_REQUEST_FINISHED: {
    return state
      .set('dropboxIsLoading', false);
  }

  case GDRIVE_REQUEST_STARTED: {
    return state
      .set('googleDriveIsLoading', true);
  }

  case GDRIVE_REQUEST_FINISHED: {
    return state
      .set('googleDriveIsLoading', false);
  }

  case GET_ACCESS: {
    return state.merge({
      ... action.data,
    });
  }

  case GET_SUCCESS: {
    return state.merge({
      isInitialized: true,
      ... action.data,
      email_notification_customized: !isSameState(action.data),
      email_notification_active: (
          isSameState(action.data) &&
          action.data.comment_mention_notification
          // As isSameStatemakes sure the attributes are the same,
          // picking a sample represents what the state should be
      )
    });
  }

  case UPDATE_SETTING_SUCCESS: {
    return state.merge({
      isInitialized: true,
      ... action.data,
      email_notification_customized: !isSameState(action.data),
      email_notification_active: (
          isSameState(action.data) &&
          action.data.comment_mention_notification
          // As isSameState makes sure the attributes are the same,
          // picking a sample represents what the state should be
      )
    });
  }

  case GET_ANALYSIS_OPTIONS_SUCCESS: {
    return state.set('analysis_options', new Map(action.data))
  }

  case TOGGLE_ANALYSIS_OPTIONS_SUCCESS: {
    return state.update('analysis_options', options => options.set(action.option, action.active));
  }

  default: {
    return state
  }
  }
};
