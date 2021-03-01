import axios from 'axios';
import { Map, List } from 'immutable';
import qs from 'qs';
import moment from 'moment';

// App
import { MODULE_NAME } from 'common/utils/constants';
import { Notification } from 'common/redux/modules/transientnotification';
import log from 'utils/logging';

const Intercom = window.Intercom;

// CONSTANTS
const DOCUMENT_URL = '/api/v1/document';
const PROJECTS_URL = 'api/v1/user/me/projects';
const USERS_URL = 'api/v1/user/me/actual_collaborators';
const CURRENT_NAME = 'project';

// ACTION CONSTANTS
const GET_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_REQUEST`;
const GET_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_SUCCESS`;
const GET_DETAILS_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_DETAILS_REQUEST`;
const GET_DETAILS_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_DETAILS_SUCCESS`;
const GET_ERROR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_ERROR`;
const SET_FILTERS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SET_FILTERS`;
const DELETE_PROJECT_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/DELETE_PROJECT_SUCCESS`;
const REJECT_PROJECT_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/REJECT_PROJECT_SUCCESS`;
const UPDATE_CURRENT = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/UPDATE_CURRENT`;
const UPDATE_PAGE = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/UPDATE_PAGE`;
const CLEAR_CACHE = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/CLEAR_CACHE`;
const ADD_COLLABORATOR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/ADD_COLLABORATOR`;
const REMOVE_COLLABORATOR = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/REMOVE_COLLABORATOR`;
const SET_LOADING = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SET_LOADING`;
const GET_USERS_REQUEST = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_USERS_REQUEST`;
const GET_USERS_SUCCESS = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/GET_USERS_SUCCESS`;

const MAX_PER_PAGE = 6;

const getRejectUrl = uuid => `${DOCUMENT_URL}/${uuid}/received_invitations`;

const getDetailsUrl = batchId => `/api/v1/batch/${batchId}`;
const getDetailsInvitedUrl = uuid => `${DOCUMENT_URL}/${uuid}`;

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

const getError = () => {
  return {
    type: GET_ERROR
  }
};

export const setFilters = filters => {
  return {
    type: SET_FILTERS,
    filters
  }
}

const getDetailsRequest = () => {
  return {
    type: GET_DETAILS_REQUEST
  }
};

const getDetailsSuccess = () => {
  return {
    type: GET_DETAILS_SUCCESS
  }
};

const deleteProjectSuccess = () => {
  return {
    type: DELETE_PROJECT_SUCCESS
  }
};

const rejectProjectSuccess = () => {
  return {
    type: REJECT_PROJECT_SUCCESS
  }
};

export const updateCurrent = (data) => {
  return {
    type: UPDATE_CURRENT,
    data
  }
}

export const updatePage = (page) => {
  return {
    type: UPDATE_PAGE,
    page
  }
}

export const clearCache = () => {
  return {
    type: CLEAR_CACHE
  }
}

export const addCollaborator = () => {
  return {
    type: ADD_COLLABORATOR
  }
}

export const setLoadingState = () => {
  return {
    type: SET_LOADING
  }
}

export const removeCollaborator = () => {
  return {
    type: REMOVE_COLLABORATOR
  }
}

const getUsersRequest = () => {
  return {
    type: GET_USERS_REQUEST
  }
}

const getUsersSuccess = data => {
  return {
    type: GET_USERS_SUCCESS,
    data
  }
}

// Async actions
export const getFromServer = (clear=true, filters) => {
  return (dispatch, getState) => {
    const state = getState();
    const project = state.project;
    const page = project.get('page');
    const rpp = project.get('rpp');
    const mergedFilters = Object.assign({}, defaultFilters, filters);
    const { q, track, owned, invited, comments, learners, keywords } = mergedFilters;

    if (clear === true) {
      dispatch(clearCache())
    }
    dispatch(getRequest());
    dispatch(setLoadingState());
    return axios(PROJECTS_URL, {
      params: { q, page, rpp, owned, invited, track, comments, learners, keywords },
      paramsSerializer(params) {
        return qs.stringify(params, { arrayFormat: 'repeat' })
      }
    })
      .then(response => {
        dispatch(getSuccess(response.data))
      }).catch((err) => {
        dispatch(getError())
        log.error(err.response || err);
        throw err;
      });
  }
};

export const getDocumentDetails = ({ batchId, uuid }) => {
  return dispatch => {
    const url = batchId ? getDetailsUrl(batchId) : getDetailsInvitedUrl(uuid);
    dispatch(getDetailsRequest())
    return axios.get(url)
      .then(dispatch(getDetailsSuccess()))
  }
}

export const deleteDocument = (info) => {
  const { batch, batch_id } = info;
  var successMessage = '';
  var errorMessage = '';
  if (batch) {
    successMessage = 'Batch of documents was deleted.';
    errorMessage = 'Batch of documents could not be deleted.';
  } else {
    successMessage = `Document ${info.title} was deleted.`;
    errorMessage = `${info.title} could not be deleted.`
  }
  Intercom('trackUserEvent', 'delete-document');
  return (dispatch, getState) => {
    const state = getState();
    const filters = state.project.get('filters').toJS();
    return axios.delete(`/api/v1/batch/${batch_id}`)
      .then(response => {
        dispatch(deleteProjectSuccess(response.data));
        dispatch(getFromServer(true, filters));
        dispatch(Notification.success(successMessage));
      }).catch((err) => {
        log.error(err.response || err);
        dispatch(Notification.error(errorMessage));
      });
  }
};

export const rejectDocument = (info) => {
  Intercom('trackUserEvent', 'reject-document');
  return (dispatch, getState) => {
    const state = getState();
    const filters = state.project.get('filters').toJS();
    return axios.delete(getRejectUrl(info.uuid))
      .then(response => {
        dispatch(rejectProjectSuccess(response.data));
        dispatch(getFromServer(true, filters));
        dispatch(Notification.success(`Document ${info.title} was rejected.`));
      }).catch((err) => {
        log.error(err.response || err);
        dispatch(Notification.error(`${info.title} could not be rejected.`));
      });
  }
};

export const getPage = (data) => {
  return (dispatch, getState) => {
    const state = getState();
    const project = state.project;
    const meta = state.project.get('meta').toJS();
    const cache = project.get('cache');
    const query = project.get('query');
    const filters = project.get('filters').toJS();
    let page = null;

    if (data.prev) {
      page = meta.prev_page;
    } else if (data.next) {
      page = meta.next_page;
    } else if (data.page !== undefined) { // Page can be 0
      page = data.page;
    }

    if (page === null || page === undefined) return;

    const cachedPage = cache.getIn([query, page]);

    if (cachedPage) {
      dispatch(updateCurrent({
        current: cachedPage,
        meta: Map(cachedPage.get('meta').pagination),
        page,
        query
      }));
    } else {
      dispatch(updatePage(page));
      dispatch(setLoadingState());
      dispatch(getFromServer(false, filters));
    }
  }
}

export const changeOwner = (uuid, owner) => {
  Intercom('trackUserEvent', 'change-owner');
  return (dispatch) => {
    return axios.post(`${DOCUMENT_URL}/${uuid}/owner`, { owner })
      .then(() => {
        dispatch(getFromServer());
      }).catch((err) => {
        log.error(err.response || err);
        dispatch(Notification.error(`Changing owner ${owner} failed`));
      })
  }
}

export const exportBatch = (batch, params) => {
  return () => {
    return axios.post(`/api/v1/batch/${batch}/prepare_export`, params)
  }
}

export const exportDocument = (uuid, params) => {
  return () => {
    return axios.post(`/api/v1/document/${uuid}/prepare_export`,params);
  }
}

export const inviteUser = (uuid, invitee) => {
  Intercom('trackUserEvent', 'invite-collaborator');
  return (dispatch) => {
    return axios.post(`${DOCUMENT_URL}/${uuid}/issued_invitations?external=True`, { invitee })
      .then(response => {
        dispatch(addCollaborator(response.data.objects[0]));
        dispatch(getFromServer());
        dispatch(Notification.success(`${invitee} was invited to collaborate.`));
      }).catch((err) => {
        log.error(err.response || err);
        dispatch(Notification.error(`Invite to ${invitee} failed.`));
      })
  }
}

export const unInviteUser = (uuid, email) => {
  Intercom('trackUserEvent', 'uninvite-collaborator');
  return (dispatch) => {
    const url = `${DOCUMENT_URL}/${uuid}/issued_invitations?external=True`;
    return axios({
      method: 'delete',
      url,
      data: { email: email }
    }).then(() => {
      dispatch(removeCollaborator());
      dispatch(getFromServer());
    }).catch((err) => {
      log.error(err.response || err);
      dispatch(Notification.error(`${email} was not successfully removed from the document.`));
    })
  }
}

export const getUsers = () => {
  return dispatch => {
    dispatch(getUsersRequest());
    return axios.get(USERS_URL)
      .then(response => {
        dispatch(getUsersSuccess(response.data));
      }).catch((err) => {
        log.error(err.response || err);
      });
  }
}

// HELPERS
const isToday = date => moment(date).isSame(new Date(), 'day');

const isSameYear = date => moment(date).isSame(new Date(), 'year');

export const projectsByDate = projects => {
  return projects.reduce((result, project) => {
    const date = project.created || project.document.created;
    let format, formatted;

    if (isToday(date)) {
      formatted = 'Today'
    } else {
      format = isSameYear(date) ? 'D MMM' : 'D MMM YYYY';
      formatted = moment(date).format(format);
    }

    result[formatted] = result[formatted] ? result[formatted].concat([project]) : [project];
    return result;
  }, {});
}

export const isFiltersDirty = filters => {
  for (let f in filters) {
    if (filters[f] !== defaultFilters[f]) {
      return true;
    }
  }

  return false;
}

// coerse string values got from query string to proper types
export const parseFilters = filters => {
  const result = {};
  for (let f in filters) {
    switch (filtersTypes[f]) {
    case 'boolean':
      result[f] = filters[f] === 'true';
      break;

    case 'object':
      result[f] = typeof filters[f] === 'object' ? filters[f] : [ filters[f] ];
      break;

    case 'string':
    default:
      result[f] = filters[f];
    }
  }
  return result;
}

// remove filters with default values before saving to url
export const clearFiltersForUrl = filters => {
  const result = {};
  for (let f in filters) {
    if (
      (filtersTypes[f] === 'object' && filters[f].length === 0) || // [] === [] => false
      (filters[f] !== defaultFilters[f])
    ) result[f] = filters[f];
  }

  return result;
}

export const defaultFilters = {
  q: '',
  track: false,
  owned: true,
  invited: true,
  comments: [],
  learners: [],
  keywords: []
};

export const filtersTypes = {
  q: 'string',
  track: 'boolean',
  owned: 'boolean',
  invited: 'boolean',
  comments: 'object',
  learners: 'object',
  keywords: 'object'
}

// REDUCERS
const initialState = Map({
  cache: Map({}),
  isInitialized: false,
  isLoading: false,
  page: 0,
  query: '',
  filters: Map(defaultFilters),
  users: List([]),
  meta: Map({}),
  current: Map({}),
  rpp: MAX_PER_PAGE,
  MAX_PER_PAGE
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case SET_LOADING: {
    return state.set('isLoading', true)
  }

  case GET_SUCCESS: {
    const meta = action.data.meta;

    return state.merge({
      isInitialized: true,
      isLoading: false,
      meta: meta.pagination,
      page: meta.pagination.page,
      query: meta.search.query,
      current: Map(action.data),
      cache: state.get('cache').setIn([meta.search.query, meta.pagination.page], Map(action.data))
    })
  }

  case GET_ERROR: {
    return state.set('isLoading', false)
  }

  case SET_FILTERS: {
    return state.set('filters', Map(action.filters));
  }

  case UPDATE_CURRENT: {
    return state.merge(action.data)
  }

  case UPDATE_PAGE: {
    return state.merge({
      page: action.page
    })
  }

  case CLEAR_CACHE: {
    return state.merge({
      cache: Map({})
    });
  }

  case ADD_COLLABORATOR: {
    return state
  }

  case REMOVE_COLLABORATOR: {
    return state
  }

  case GET_USERS_SUCCESS: {
    return state.set('users', List(action.data))
  }

  default: {
    return state
  }
  }
};
