// CONSTANTS
import * as CleanupDocumentConstants from 'CleanupDocument/redux/constants';

// ACTION'S GENERATOR
const filterUpdateGen = (value) => {
  return {
    type: CleanupDocumentConstants.FILTER_UPDATE,
    value
  }
};

const checkFileGen = (uri, checked) => {
  return {
    type: CleanupDocumentConstants.CHECK_FILE,
    uri, checked
  }
};

const dragTool = (tool) => {
    return {
      type: CleanupDocumentConstants.MANAGE_DRAG,
      tool
    }
}

const dropTool = (tool, to_selected) => {
    return {
      type: CleanupDocumentConstants.MANAGE_DROP,
      tool, to_selected
    }
};

const blockSelectedDocs = (doc_ids) => {
    return {
        type: CleanupDocumentConstants.BLOCK_DOCUMENT,
        doc_ids
    }
}


export function updateFilter(value) {
  return dispatch => dispatch(filterUpdateGen(value))
}

export function setState(file, checked) {
  return dispatch => dispatch(checkFileGen(file, checked))
}

export function manageDrag(tool, selected) {
  return dispatch => dispatch(dragTool(tool))
}

export function manageDrop(tool, selected) {
  return dispatch => dispatch(dropTool(tool, selected))
}

export function blockDocs(doc_ids) {
  return dispatch => dispatch(blockSelectedDocs(doc_ids))
}
