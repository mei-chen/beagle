import { Map, List } from 'immutable';
import * as BatchManagementConstants from 'BatchManagement/redux/constants';
import { GET_REQUEST, GET_SUCCESS } from 'base/redux/actions';
import { transferTo } from 'base/utils/misc';
import { pushMessage } from 'Messages/actions';

const initialState = Map({
  batches: new List(),
  ready: false,
  isFormModalOpen: false,
  isUserManagementModalOpen: false,
  editBatch: null,
  boundFiles: new List(),
  unboundFiles: new List(),
  collaborators_ready: false,
  collaborators_error: false,
  collaborators: List()
});

const batchReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_REQUEST('batch'):
    {
      return state.merge({
        ready: false
      })
    }


    case GET_SUCCESS('batch'):
    {
      return state.merge({
        ready: true,
        batches: List(action.data)
      });
    }

    case GET_SUCCESS('filesOfBatch'):
    {
      return state.merge({
        [action.key]: List(action.data)
      });
    }

    case BatchManagementConstants.BIND_FILES:
    {
      let [ unboundFiles, boundFiles ] = transferTo(
        state.get('unboundFiles'), state.get('boundFiles'),
        (el) => el.resource_uri !== action.uri
      );
      return state.merge({
        boundFiles,
        unboundFiles
      });
    }

    case BatchManagementConstants.UNBIND_FILES:
    {
      let [ boundFiles, unboundFiles ] = transferTo(
        state.get('boundFiles'), state.get('unboundFiles'),
        (el) => el.resource_uri !== action.uri
      );
      return state.merge({
        boundFiles,
        unboundFiles
      });
    }

    case BatchManagementConstants.FORM_SHOW:
    {
      return state.merge({
        isFormModalOpen: true,
        editBatch: action.batch
      })
    }

    case BatchManagementConstants.FORM_CLOSE:
    {
      return state.merge({
        isFormModalOpen: false
      })
    }

    case BatchManagementConstants.COLLABORATORS_MANAGEMENT_SHOW:
    {
      return state.merge({
        isUserManagementModalOpen: true,
      })
    }

    case BatchManagementConstants.COLLABORATORS_MANAGEMENT_CLOSE:
    {
      return state.merge({
        isUserManagementModalOpen: false,
      })
    }

    case BatchManagementConstants.GET_COLLABORATORS_REQUEST:
    {
      return state.merge({
        collaborators_ready: false,
      })
    }

    case BatchManagementConstants.GET_COLLABORATORS_SUCCESS:
    {
      return state.merge({
        collaborators_ready: true,
        collaborators: List(action.data.collaborators)
      })
    }

    case BatchManagementConstants.GET_COLLABORATORS_ERROR:
    {
      return state.merge({
        collaborators_ready: true,
        collaborators_error: true
      })
    }

    case BatchManagementConstants.POST_COLLABORATOR_SUCCESS:
    {
      return state;
    }

    case 'batchForProject/ProjectManagement/GET_SUCCESS':
    {
      return state.merge({
        batches: List(action.data)
      });
    }

    default:
      return state
  }
};

export default batchReducer;
