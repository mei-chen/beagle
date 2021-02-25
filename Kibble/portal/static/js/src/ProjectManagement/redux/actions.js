import { getBatches, patchBatch } from 'base/redux/modules/batches';
import * as ProjectManagementConstants from 'ProjectManagement/redux/constants';

import {
  getFromServer,
  postToServer,
  patchToServer
} from 'base/redux/requests';
const ENDPOINT = window.CONFIG.API_URLS.projectList;

const bindBatchGen = (uri) => {
  return {
    type: ProjectManagementConstants.BIND_BATCH,
    uri
  }
};

const unbindBatchGen = (uri) => {
  return {
    type: ProjectManagementConstants.UNBIND_BATCH,
    uri
  }
};

const requestCollaboratorsSuccess = (collaborators) => {
  return {
    type : ProjectManagementConstants.GET_COLLABORATORS_SUCCESS,
    data: collaborators
  }
}

const requestCollaboratorsError = () => {
  return {
    type : ProjectManagementConstants.GET_COLLABORATORS_ERROR
  }
}

const postCollaboratorSuccess = () => {
  return {
    type : ProjectManagementConstants.POST_COLLABORATOR_SUCCESS,
  }
}

const postCollaboratorError = () => {
  return {
    type : ProjectManagementConstants.POST_COLLABORATOR_ERROR
  }
}


export function setModalOpen(modal, isOpen) {
  return dispatch => dispatch({
    type: ProjectManagementConstants.SET_MODAL_OPEN,
    data: { modal, isOpen }
  });
}

export function getBatchForProject(project) {
  return dispatch => {
    dispatch(getBatches({ project }, {
      type: 'batchOfProject',
      key: 'boundBatches'
    }));
  }
}

export function getFreeBatches(project) {
  return dispatch => {
    dispatch(getBatches({ unassigned: project }, { type: 'batchOfProject', key: 'unboundBatches' }));
  }
}

export function addBatchProject(batch_uri, project_uri) {
  return dispatch => {
    dispatch(patchBatch(batch_uri, { add_project: [ project_uri ] }, () => bindBatchGen(batch_uri)));
  }
}

export function delBatchProject(batch_uri, project_uri) {
  return dispatch => {
    dispatch(patchBatch(batch_uri, { remove_project: [ project_uri ] }, () => unbindBatchGen(batch_uri)));
  }
}

export function selectProject(data) {
  return dispatch => dispatch({
    type: ProjectManagementConstants.SELECT_PROJECT, data
  })
}

export function deselectProject() {
  return dispatch => dispatch({
    type: ProjectManagementConstants.DESELECT_PROJECT
  })
}

export function setShowInactive(data) {
  return dispatch => {
    dispatch(deselectProject());
    dispatch({
      type: ProjectManagementConstants.SET_SHOW_INACTIVE,
      data
    });
  }
}

export function getInactiveProject(data) {
  return dispatch => dispatch({
    type: ProjectManagementConstants.GET_INACTIVE_PROJECT_SUCCESS,
    data
  })
}

export function addToInactiveProject(data) {
  return dispatch => dispatch({
    type: ProjectManagementConstants.ADD_TO_INACTIVE_PROJECT,
    data
  })
}

export const requestCollaborators = () => {
  return {
    type : ProjectManagementConstants.GET_COLLABORATORS_REQUEST
  }
}

export function getCollaboratorsForProject(id,data={}) {
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
errorEvent = postCollaboratorError, callbacks = () => getCollaboratorsForProject(id)) {
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
errorEvent = postCollaboratorError, callbacks = () => getCollaboratorsForProject(id)) {
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
