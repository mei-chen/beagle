import { Map, List } from 'immutable';
import { transferTo } from 'base/utils/misc';
import * as ProjectManagementReduxConstants from 'ProjectManagement/redux/constants';
import { GET_REQUEST, GET_SUCCESS, GET_ERROR, POST_REQUEST, POST_SUCCESS, POST_ERROR } from 'base/redux/actions';


const initialState = Map({
  isFormModalOpen: false,
  boundBatches: new List(),
  unboundBatches: new List(),
  batchFilterValue: '',
  selectedProject: new Map(),
  inactiveProjects: new List(),
  isShowInactive: false,
  transferToInactive: new List(),
  isModalOpen: new Map({
    create: false,
    edit: false,
    archive: false,
    collaborators: false
  }),
  collaborators_ready: false,
  collaborators_error: false,
  collaborators: List()
});

const projectsReducer = (state = initialState, action) => {
  switch (action.type) {

    case GET_SUCCESS('batchOfProject'):
    {
      return state.merge({ [action.key]: List(action.data) })
    }

    case ProjectManagementReduxConstants.SELECT_PROJECT:
    {
      return state.merge({ selectedProject: Map(action.data) })
    }

    case ProjectManagementReduxConstants.ADD_TO_INACTIVE_PROJECT:
    {
      return state
        .update('inactiveProjects', list => list.push(action.data))
        .update('transferToInactive', list => list.filter(id => id != action.data.id))
    }

    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action !== 'compress_project') {
        return state
      }
      return state.update('transferToInactive', list => list.push(msg.project_id))
    }

    case POST_ERROR('project'):
    case POST_ERROR('batch'):
    {
      return state.merge({
        isFormModalOpen: false
      })
    }

    case ProjectManagementReduxConstants.GET_INACTIVE_PROJECT_SUCCESS:
    {
      return state.merge({ inactiveProjects: List(action.data) })
    }

    case ProjectManagementReduxConstants.SET_SHOW_INACTIVE:
    {
      return state.merge({
        isShowInactive: action.data
      })
    }

    case ProjectManagementReduxConstants.DESELECT_PROJECT:
    {
      return state.merge({ selectedProject: new Map() })
    }


    case ProjectManagementReduxConstants.FILTER_UPDATE:
    {
      return state.set('batchFilterValue', action.value);
    }


    case ProjectManagementReduxConstants.BIND_BATCH:
    {
      let [ unboundBatches, boundBatches ] = transferTo(
        state.get('unboundBatches'), state.get('boundBatches'),
        (el) => el.resource_uri !== action.uri
      );
      return state.merge({ boundBatches, unboundBatches })
    }

    case ProjectManagementReduxConstants.UNBIND_BATCH:
    {
      let [ boundBatches, unboundBatches ] = transferTo(
        state.get('boundBatches'), state.get('unboundBatches'),
        (el) => el.resource_uri !== action.uri
      );
      return state.merge({ boundBatches, unboundBatches })
    }

    case ProjectManagementReduxConstants.SET_MODAL_OPEN:
    {
      return state.setIn([ 'isModalOpen', action.data.modal ], action.data.isOpen)
    }

    case ProjectManagementReduxConstants.GET_COLLABORATORS_REQUEST:
    {
      return state.merge({
        collaborators_ready: false,
      })
    }

    case ProjectManagementReduxConstants.GET_COLLABORATORS_SUCCESS:
    {
      return state.merge({
        collaborators_ready: true,
        collaborators: List(action.data.collaborators)
      })
    }

    case ProjectManagementReduxConstants.GET_COLLABORATORS_ERROR:
    {
      return state.merge({
        collaborators_ready: true,
        collaborators_error: true
      })
    }

    case ProjectManagementReduxConstants.POST_COLLABORATOR_SUCCESS:
    {

    }

    default:
    {
      return state
    }
  }
};

export default projectsReducer;
