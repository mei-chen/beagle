import { List } from 'immutable'
import {
  getFromServer,
  postToServer,
  patchToServer
} from 'base/redux/requests';
import {
  GET_REQUEST,
  GET_SUCCESS,
  GET_ERROR,
  POST_REQUEST,
  POST_SUCCESS,
  POST_ERROR,
  PATCH_REQUEST,
  PATCH_SUCCESS,
  PATCH_ERROR,
  TASK_RUN,
  TASK_ERROR,
  REMOVE
} from 'base/redux/actions';
import { pushMessage } from 'Messages/actions';

const ENDPOINT = window.CONFIG.API_URLS.projectList;

// GET
const getProjectRequest = () => {
  return {
    type: GET_REQUEST('project')
  };
}

const getProjectSuccess = (data) => {
  return {
    type: GET_SUCCESS('project'),
    data
  };
}

const getProjectError = (err) => {
  return {
    type: GET_ERROR('project'),
    err
  };
}


// POST
const postProjectRequest = () => {
  return {
    type: POST_REQUEST('project')
  };
}

const postProjectSuccess = (data) => {
  return {
    type: POST_SUCCESS('project'),
    data
  };
}

const postProjectError = (err) => {
  return {
    type: POST_ERROR('project'),
    err
  };
}


// PATCH
const patchProjectRequest = () => ({
  type: PATCH_REQUEST('project')
});

const patchProjectSuccess = (payload) => ({
  type: PATCH_SUCCESS('project'),
  payload
});

const patchProjectError = (payload) => ({
  type: PATCH_ERROR('project'),
  payload
});
// ---------

export const getProjects = (data = {}, successEvent = getProjectSuccess) => {
  return getFromServer(
    ENDPOINT, data, getProjectRequest, successEvent, getProjectError);
}

export const postProjects = (data, successEvent = postProjectSuccess) => {
  return postToServer({
    endpoint: ENDPOINT,
    data,
    processEvent: postProjectRequest,
    successEvent,
    callbacks: [getProjects]
  });
};

export const patchProject = (data, id, callbacks) => {
  return patchToServer({
    endpoint: `${ENDPOINT}${id}/`,
    data,
    processEvent: patchProjectRequest,
    successEvent: patchProjectSuccess,
    callbacks
  })
};

export const archiveProject = (id, callbacks) => {
  return patchToServer({
    endpoint: `${ENDPOINT}${id}/compress/`,
    successEvent() {
      return pushMessage('Task created.', 'info')
    },
    errorEvent: (error) => pushMessage(`Cannot create task. ${error}`, 'error'),
    callbacks
  })
};

export const removeProject = (id) => ({ type: REMOVE('project'), id });


// REDUCERS
const initialState = List();


export default (state = initialState, action) => {
  switch (action.type) {

    case GET_SUCCESS('project'):
    {
      return List(action.data);
    }

    case POST_SUCCESS('project'):
    {
      return state.push(action.data)
    }

    case PATCH_SUCCESS('project'):
    {
      return state.map(project => {
        if (project.id == action.payload.id) {
          return action.payload
        } else return project
      })
    }

    case REMOVE('project'):
    {
      return state.filter(project => project.id !== action.id)
    }

    case 'WEBSOCKET':
    {
      const ws_msg = action.data.message;
      if (ws_msg.action !== 'compress_project') return state;
      return state.map(project => {
        if (project.id !== ws_msg.project_id) return project;
        project.archive = ws_msg.archive;
        return project
      })
    }

    default:
    {
      return state;
    }
  }
};
