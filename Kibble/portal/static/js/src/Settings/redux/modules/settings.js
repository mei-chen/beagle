import axios from 'axios';
import { Map, List } from 'immutable';
import Cookies from "universal-cookie";
const axiosConf = { headers: { 'Content-Type': 'application/json' } };
const cookies = new Cookies();

// App
import { MODULE_NAME } from 'Settings/redux/constants';
const CURRENT_NAME = 'Settings';

// ACTION CONSTANTS
const GET_REQUEST = `${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_CUSTOM_PERSONAL_DATA_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_CUSTOM_PERSONAL_DATA_SUCCESS`;
const GET_ACCESS = `${MODULE_NAME}/${CURRENT_NAME}/GET_ACCESS`;
const CHANGE_SUCCESS = `${MODULE_NAME}/${CURRENT_NAME}/CHANGE_SUCCESS`;
const CHANGE_FAIL = `${MODULE_NAME}/${CURRENT_NAME}/CHANGE_FAIL`;
const SET_MODAL_OPEN = `${MODULE_NAME}/${CURRENT_NAME}/SET_MODAL_OPEN`;
const SET_ALL_ASS = `${MODULE_NAME}/${CURRENT_NAME}/SET_ALL_ASS`;

const URL_BASE = '/api/v1/profile/';
const CUSTOM_PERSONAL_DATA_URL = '/api/v1/custom-personal-data/';

const getRequest = () => {
  return {
    type: GET_REQUEST
  };
};

const getSuccess = (data) => {
  return {
    type: GET_SUCCESS,
    data
  };
};

const getCustomPersonalDataSuccess = (data) => {
  return {
    type: GET_CUSTOM_PERSONAL_DATA_SUCCESS,
    data
  };
};

const changeSuccess = () => {
  return {
    type: CHANGE_SUCCESS
  };
};

const changeFail = () => {
  return {
    type: CHANGE_FAIL
  };
};

const getAccess = (data) => {
  return {
    type: GET_ACCESS,
    data
  }
};

export const setModalOpen = (open) => {
  return {
    type: SET_MODAL_OPEN,
    open: open
  }
}

// Async actions
export const getFromServer = () => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(URL_BASE)
      .then((response) => {
        dispatch(getSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  };
};

export const getCustomPersonalData = () => {
  return (dispatch) => {
    dispatch(getRequest());
    return axios.get(CUSTOM_PERSONAL_DATA_URL)
      .then((response) => {
        dispatch(getCustomPersonalDataSuccess(response.data));
      }).catch((err) => {
        console.error(err.response || err);
        throw err;
      });
  };
}

export const changeSetting = (setting,state) => {
  return dispatch => {
    dispatch(getRequest());
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.patch(URL_BASE, {[setting]:state}, Object.assign({}, axiosConf))
      .then(response => {
        dispatch(getFromServer());
        dispatch(changeSuccess());
      }).catch((err) => {
        dispatch(changeFail());
        console.log(err.response || err);
        throw err;
      });
  }
};

export const addPersonalDataType = (type, text, is_regex) => {
  return dispatch => {
    dispatch(getRequest());
    const data = {type: type, text: text, is_rgx: is_regex};
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.post(CUSTOM_PERSONAL_DATA_URL, data , Object.assign({}, axiosConf))
      .then(response => {
        dispatch(getFromServer());
        dispatch(getCustomPersonalData());
        dispatch(changeSuccess());
      }).catch((err) => {
        dispatch(changeFail());
        console.log(err.response || err);
        throw err;
      });
  }
}


export const deletePersonalDataType = (uuid) => {
  return dispatch => {
    dispatch(getRequest());
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.delete(CUSTOM_PERSONAL_DATA_URL+uuid, Object.assign({}, axiosConf))
      .then(response => {
        dispatch(getFromServer());
        dispatch(getCustomPersonalData());
        dispatch(changeSuccess());
      }).catch((err) => {
        dispatch(changeFail());
        console.log(err.response || err);
        throw err;
      });
  }
}

// REDUCERS
const initialState = {
  isInitialized: false,
  isModalOpen:false,
  id:undefined,
  file_auto_process: false,
  obfuscated_export_ext:undefined,
  personal_data_types: {},
  auto_gather_personal_data: false,
  sentence_word_threshold: false,
  obfuscate_type: undefined,
  obfuscate_string: undefined,
  highlight_color: undefined,
  auto_cleanup_tools: [],
  user:undefined,
  change_success: undefined,
  isInitializedCustomPersonalData: false,
  custom_personal_data: [],
  custom_type_names: [],
  set_all_personal_data: []
};


export default (state = initialState, action = {}) => {
  switch (action.type) {
    case GET_REQUEST: {
      return {...state, change_success:undefined}
    }

    case GET_SUCCESS: {
      return {
        ...state,
        isInitialized: true,
        ...action.data,
      };
    }

    case GET_CUSTOM_PERSONAL_DATA_SUCCESS: {
      var custom_personal_data = action.data;
      var type_names = new Set();
      custom_personal_data.filter(item => {
        !type_names.has(item.type) && type_names.add(item.type)
      });
      type_names = Array.from(type_names);
      return {
        ...state,
        isInitializedCustomPersonalData: true,
        custom_personal_data: custom_personal_data,
        custom_type_names: type_names
      };
    }

    case CHANGE_SUCCESS: {
      return {
        ...state,
        change_success: 'success',
      };
    }

    case CHANGE_FAIL: {
      return {
        ...state,
        change_success: 'fail',
      };
    }

    case SET_MODAL_OPEN: {
      return {
        ...state,
        isModalOpen: action.open,
        change_success: undefined,
      };
    }

    case GET_ACCESS: {
      return {
        ...state,
        ... action.data,
      };
    }


    default: {
      return state;
    }
  }
};
