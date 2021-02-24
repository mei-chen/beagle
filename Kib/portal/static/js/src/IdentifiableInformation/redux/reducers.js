import { Map, List, setIn } from 'immutable';
import * as baseReduxActions from 'base/redux/actions';
import * as personalReduxActions from 'IdentifiableInformation/redux/constants'

import uuid from 'uuid';

const initialState = Map({
  trigger_props: uuid.v4(),
  displayed_document_id: null,
  isInitialized: false,
  gathering_status: null,
  personalData: List(),
  batches: List(),
  files: List(),
  files_data: Map({})
});
export default (state = initialState, action) => {

  switch (action.type) {
    case 'WEBSOCKET':
    {
      const message = action.data.message;
      if (message.status === 'completed') {
        return state.merge({
          gathering_status: 'completed'
        })
      }
    }

    case baseReduxActions.GET_REQUEST('IdentifiableInformation'):
    {
      return state.merge({
        isInitialized: false
      })
    }

    case baseReduxActions.GET_SUCCESS('IdentifiableInformation'):
    {
      return state.merge({
        isInitialized:true,
        personalData: new List(action.data)
      })
    }

    case 'docsForBatch/personal_data/GET_SUCCESS':
    {
      return state.merge({
        files: List(action.data),
      });
    }

    case 'batchForProject/personal_data/GET_SUCCESS':
    {
      return state.merge({
        batches: List(action.data)
      });
    }

    case personalReduxActions.INITIALIZE_FILE_DATA:
    {
      return state.setIn(['files_data',action.id.toString()],Map({
          isLoadingPersonalData: false,
          isLoadingStatistics: false,
          statistics: {},
          personalData:{}
        }));
    }

    case personalReduxActions.SET_ACTIVE_INFO_BOX:
    {
      return state.merge({
        displayed_document_id: action.id,
      })
    }

    case personalReduxActions.SET_LOADING_DATA_GATHERING:
    {
      return state.merge({
        gathering_status: action.status,
      })
    }

    case personalReduxActions.GET_STATISTICS_FOR_DOC_REQUEST:
    {
      return state.setIn(['files_data',action.id.toString(),'isLoadingStatistics'], true);
    }

    case personalReduxActions.GET_STATISTICS_FOR_DOC_SUCCESS:
    {
      return state.setIn(['files_data',action.id.toString(),'statistics'],action.data);
    }

    case personalReduxActions.SET_STATISTICS_LOADING_OFF:
    {
      return state.setIn(['files_data',action.id.toString(),'isLoadingStatistics'],false);
    }

    case personalReduxActions.GET_PERSONAL_DATA_FOR_DOC_REQUEST:
    {
      return state.setIn(['files_data',action.id.toString(),'isLoadingPersonalData'], true);
    }

    case personalReduxActions.GET_PERSONAL_DATA_FOR_DOC_SUCCESS:
    {
      return state.setIn(['files_data',action.id.toString(),'personalData'],action.data);
    }

    case personalReduxActions.SET_PERSONAL_DATA_LOADING_OFF:
    {
      return state.setIn(['files_data',action.id.toString(),'isLoadingPersonalData'],false);
    }

    case personalReduxActions.SET_PERSONAL_DATA_ENTRY_SUCCESS:
    {
      return state.updateIn(
        ['files_data',action.id.toString(),'personalData'],
        (entries) => {
          entries[action.idx] = action.data
          return entries;
        }
      );
    }

    case personalReduxActions.TRIGGER_PERSONAL_DATA_ENTRY:
    {
      return state.merge({
        trigger_props: uuid.v4()
      });
    }

    default:
    {
      return state
    }

  }
}
