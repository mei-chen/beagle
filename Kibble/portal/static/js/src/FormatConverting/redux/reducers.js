import { Map, List } from 'immutable';
import * as FormatConvertingReduxConstants from 'FormatConverting/redux/constants';
import { GET_REQUEST, GET_SUCCESS } from 'base/redux/actions';
import {MODULE_NAME} from 'FormatConverting/constants';


// HELPERS
const isResponseSuccess = (isResponseSuccess) => ({
  isDataTransferring: false,
  isFormModalOpen: !isResponseSuccess,
  isFailOnTransferring: isResponseSuccess
});

const initialState = Map({
  project_batches: new List(),  // List of all batches
  ready: false,                 // Switch to true when batch fetch is done and ready to insert into table
  fail: false,                  // Indicate any fail on batch request fail
  isDataTransferring: false,
  isFailOnTransferring: false,
  errors: new List(),
  batch_files: [],
  batch_docs: [],
  fileState: {},
  fileFilterValue: ''
});

const formatReducer = (state = initialState, action) => {
  switch (action.type) {
    // REQUEST CASES
    case GET_REQUEST('batch'):
      return {
        ...state,
        ready: false,
        isDataTransferring: true
      };
    case GET_REQUEST('file'):
      return {
        ...state,
        ready: false,
        isDataTransferring: true
      };
    // -----------


    // REQUEST SUCCESS CASES
    case GET_SUCCESS('batchForProject' + MODULE_NAME):
      return {
        ...state,
        ready: true,
        project_batches: List(action.data),
        ...isResponseSuccess(true)
      };

    case GET_SUCCESS('filesForBatch' + MODULE_NAME):
      return {
        ...state,
        ready: true,
        batch_files: List(action.data),
        ...isResponseSuccess(true)
      };

    case GET_SUCCESS('docsForBatch' + MODULE_NAME):
      return {
        ...state,
        ready: true,
        batch_docs: List(action.data),
        ...isResponseSuccess(true)
      };

    case 'WEBSOCKET':
      const msg = action.data.message;
      const files = state.batch_files;
      if (msg.action !== 'convert_file' || files.every(x => {return x.id}).indexOf(msg.file) === -1) {
        return state;
      }
      return {
        ...state,
        batch_files: state.batch_files.filter(x => x.id !== msg.file),
        batch_docs: state.batch_docs.concat([msg.document]),
        fileState: {...fileState, [msg.file]: false}
      };

    // -----------

    case FormatConvertingReduxConstants.FILTER_UPDATE:
      return {
        ...state,
        fileFilterValue: action.value
      };

    case FormatConvertingReduxConstants.CHECK_FILE:
      const fileState = state.fileState;
      return {
        ...state,
        fileState: {...fileState, [action.uri]: action.checked}
      };

    default:
      return state
  }
};

export default formatReducer;
