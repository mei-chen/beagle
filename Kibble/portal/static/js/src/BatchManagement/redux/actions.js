import { getBatches } from 'base/redux/modules/batches';
import { getFiles, patchFile } from 'base/redux/modules/files';
import {
  getFromServer,
  postToServer,
  patchToServer
} from 'base/redux/requests';

const ENDPOINT = window.CONFIG.API_URLS.batchList;

// CONSTANTS
import * as BatchManagementConstants from 'BatchManagement/redux/constants';

// ACTION'S GENERATOR
const filterUpdateGen = (value) => {
  return {
    type: BatchManagementConstants.FILTER_UPDATE,
    value
  }
};

const bindFilesGen = (uri) => {
  return {
    type: BatchManagementConstants.BIND_FILES,
    uri
  }
};

const unbindFilesGen = (uri) => {
  return {
    type: BatchManagementConstants.UNBIND_FILES,
    uri
  }
};


const requestCollaboratorsSuccess = (collaborators) => {
  return {
    type : BatchManagementConstants.GET_COLLABORATORS_SUCCESS,
    data: collaborators
  }
}

const requestCollaboratorsError = () => {
  return {
    type : BatchManagementConstants.GET_COLLABORATORS_ERROR
  }
}

const postCollaboratorSuccess = () => {
  return {
    type : BatchManagementConstants.POST_COLLABORATOR_SUCCESS,
  }
}

const postCollaboratorError = () => {
  return {
    type : BatchManagementConstants.POST_COLLABORATOR_ERROR
  }
}

export function getFilesForBatch(batch) {
  return dispatch => {
    dispatch(getFiles({batch}, {type: 'filesOfBatch', key: 'boundFiles'}));
  }
}

export function getFreeFiles() {
  return dispatch => {
    dispatch(getFiles({unassigned: true}, {type: 'filesOfBatch', key: 'unboundFiles'}));
  }
}

export function setFileToBatch(file_uri, batch) {
  return dispatch => {
    if (batch) {
        dispatch(patchFile(file_uri, {batch}, () => bindFilesGen(file_uri)));
    } else {
        dispatch(patchFile(file_uri, {batch: null}, () => unbindFilesGen(file_uri)));
    }
  }
}

export function showForm() {
  return dispatch => dispatch({
    type: BatchManagementConstants.FORM_SHOW
  });
}

export function closeForm() {
  return dispatch => dispatch({ type: BatchManagementConstants.FORM_CLOSE });
}

export function showUserManagement() {
  return dispatch => dispatch({
    type: BatchManagementConstants.COLLABORATORS_MANAGEMENT_SHOW
  });
}

export function closeUserManagement() {
  return dispatch => dispatch({
    type: BatchManagementConstants.COLLABORATORS_MANAGEMENT_CLOSE
  });
}

export const requestCollaborators = () => {
  return {
    type : BatchManagementConstants.GET_COLLABORATORS_REQUEST
  }
}

export function getCollaboratorsForBatch(id,data={}) {
  return dispatch => dispatch(
    getFromServer(
      `${ENDPOINT}${id}/list_collaborators/`,
      data,
      null,
      requestCollaboratorsSuccess,
      requestCollaboratorsError
    )
  )
}

export function inviteCollaborator(id,data,successEvent = postCollaboratorSuccess,
errorEvent = postCollaboratorError, callbacks = () => getCollaboratorsForBatch(id)) {
  const endpoint = `${ENDPOINT}${id}/invite_collaborator/`;
  return dispatch => dispatch(
    postToServer({
      endpoint,
      data,
      successEvent,
      errorEvent,
      callbacks
    })
  )
}

export function unInviteCollaborator(id,data,successEvent = postCollaboratorSuccess,
errorEvent = postCollaboratorError, callbacks = () => getCollaboratorsForBatch(id)) {
  const endpoint = `${ENDPOINT}${id}/uninvite_collaborator/`;
  return dispatch => dispatch(
    postToServer({
      endpoint,
      data,
      successEvent,
      errorEvent,
      callbacks
    })
  )
}
