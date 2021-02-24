import { List } from 'immutable';
import axios from 'axios';
import Cookies from "universal-cookie";

import { pushLogEntry } from 'ProgressNotification/actions'

import { getFromServer, patchToServer } from 'base/redux/requests';
import * as baseReduxActions from 'base/redux/actions';
import * as personalReduxActions from 'IdentifiableInformation/redux/constants'

const axiosConf = { headers: { 'Content-Type': 'application/json' } };
const cookies = new Cookies()

const ENDPOINT = window.CONFIG.API_URLS.personalData;
const BATCH_ENDPOINT = window.CONFIG.API_URLS.batchList;

// projects request
const getPersonalDataRequest = () => {
  return {
    type: baseReduxActions.GET_REQUEST('IdentifiableInformation')
  };
};

const getPersonalDataSuccess = (data, extra) => {
  return {
    type: baseReduxActions.GET_SUCCESS('IdentifiableInformation'),
    data
  };
};

const getPersonalDataError = (err) => {
  return {
    type: baseReduxActions.GET_ERROR('IdentifiableInformation'),
    err
  };
};


const getStatisticsRequest = () => {
  return {
    type: personalReduxActions.GET_STATISTICS_REQUEST
  }
};

const getStatisticsError = () => {
  return {
    type: personalReduxActions.GET_STATISTICS_ERROR
  }
}

const getStatisticsSuccess = () => {
  return {
    type: personalReduxActions.GET_STATISTICS_SUCCESS
  }
};

const getStatisticsForDocRequest = (id) => {
  return {
    type: personalReduxActions.GET_STATISTICS_FOR_DOC_REQUEST,
    id:id
  }
};

const getStatisticsForDocError = () => {
  return {
    type: personalReduxActions.GET_STATISTICS_FOR_DOC_ERROR
  }
}

const getStatisticsForDocSuccess = (data,id) => {
  return {
    type: personalReduxActions.GET_STATISTICS_FOR_DOC_SUCCESS,
    data: data,
    id:id
  }
}

const setStatisticsLoadingOff = (id) => {
  return {
    type: personalReduxActions.SET_STATISTICS_LOADING_OFF,
    id:id
  }
}

const getPersonalDataForDocRequest = (id) => {
  return {
    type: personalReduxActions.GET_PERSONAL_DATA_FOR_DOC_REQUEST,
    id: id
  }
}

const getPersonalDataForDocError = () => {
  return {
    type: personalReduxActions.GET_PERSONAL_DATA_FOR_DOC_ERROR
  }
}

const getPersonalDataForDocSuccess = (data, id) => {
  return {
    type: personalReduxActions.GET_PERSONAL_DATA_FOR_DOC_SUCCESS,
    data: data,
    id: id
  }
}

const setPersonalDataLoadingOff = (id) => {
  return {
    type: personalReduxActions.SET_PERSONAL_DATA_LOADING_OFF,
    id: id
  }
}

export const setActiveInfoBox = (id) => {
  return {
    type: personalReduxActions.SET_ACTIVE_INFO_BOX,
    id: id
  }
}

export const initializeFileData = (id) => {
  return {
    type: personalReduxActions.INITIALIZE_FILE_DATA,
    id: id
  }
}

const setStatusDataGathering = (status) => {
  return {
    type: personalReduxActions.SET_LOADING_DATA_GATHERING,
    status: status
  }
}

const markPersonalDataEntrySuccess = (data,id,idx) => {
  return {
    type: personalReduxActions.SET_PERSONAL_DATA_ENTRY_SUCCESS,
    data: data,
    id: id,
    idx: idx
  }
}


// method to trigger changes , due to non imutable structure
// TODO = refactor
const triggerPersonalDataEntry = () => {
  return {
    type: personalReduxActions.TRIGGER_PERSONAL_DATA_ENTRY,
  }
}

export const gatherPersonalData = ( id ) => {
  return dispatch => {
    dispatch(pushLogEntry({message:"Start gathering data",level:"info"}));
    const url = BATCH_ENDPOINT+`${id}/gather_personal_data`;
    return axios.get(url)
      .then( response => {
        dispatch(setStatusDataGathering('loading'));
      })
      .catch(err => {
        dispatch(setStatusDataGathering('error'));
        dispatch(pushLogEntry({message:"Error gathering personal data",level:"error"}));
      })
  }
}

export const getStatistics = ( structure, id ) => {
  return dispatch => {
    const url = ENDPOINT+`statistics/?${structure}=${id}`;
    dispatch(getStatisticsRequest())
    return axios.get(url)
      .then(dispatch(getStatisticsSuccess()))
  }
}

export const getStatisticsForDoc = ( id ) => {
  return dispatch => {
    const url = ENDPOINT+`statistics/?document=${id}`;
    dispatch(getStatisticsForDocRequest(id))
    return axios.get(url)
      .then(response => dispatch(getStatisticsForDocSuccess(response.data, id)))
        .then(() => dispatch(setStatisticsLoadingOff(id)))
      .catch(err =>{
        console.error(err);
        dispatch(getStatisticsForDocError());
      })
  }
}

export const getPersonalData = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT,
    data,
    getPersonalDataRequest,
    getPersonalDataSuccess,
    getPersonalDataError,
    extra
  );
};

export const getPersonalDataForDoc = ( id ) => {
  return dispatch => {
    const url = ENDPOINT+`?document=${id}`;
    dispatch(getPersonalDataForDocRequest(id))
    return axios.get(url)
      .then(response => dispatch(getPersonalDataForDocSuccess(response.data, id)))
        .then(() => dispatch(setPersonalDataLoadingOff(id)))
      .catch(err => {
        console.error(err);
        dispatch(getPersonalDataForDocError());
      })
  }
}

export const markPersonalDataEntry = ( uuid, selected, id, key ) => {
  return dispatch => {
    const url = 'http://localhost:8001/api/v1/personal-data/'+`${uuid}/`;
    axiosConf.headers[ 'X-CSRFToken' ] = cookies.get('csrftoken');
    return axios.patch(url,{selected: selected}, Object.assign({}, axiosConf))
      .then(response => {
        dispatch(markPersonalDataEntrySuccess(response.data,id,key));
        dispatch(triggerPersonalDataEntry());
      })
      .catch(err => {
        console.error(err);
      })
  }
}
