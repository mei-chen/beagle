import { Map, List } from 'immutable';
import * as RegExConstants from 'RegEx/redux/constants';
import { GET_REQUEST, GET_SUCCESS } from 'base/redux/actions';

import { MODULE_NAME } from 'RegEx/constants'

const initialState = Map({
  project_batches: new List(),    // List of all batches
  regexes: new List(),            // List of available regexes
  reports: new List(),            // List of reports for current batch
  selectedRegEx: Map(),           // currently selected regex
  selectedReport:  new Map(),
  loadingReports: false,
  selectedProjectId: null,
  selectedBatchId: null,
  bulkDownloadTaskState: false,
  bulkDownloadUrl: '',
  isModalOpen: new Map({
    create: false,
    edit: false,
    delete: false,
    preview: false
  })
});

const regexReducers = (state = initialState, action) => {
  switch (action.type) {
    case GET_SUCCESS('batchForProject' + MODULE_NAME):
    {
      return state.merge({
        project_batches: new List(action.data)
      });
    }

    case GET_SUCCESS('reportsForBatch' + MODULE_NAME):
    {
      return state.merge({
        reports: List(action.data),
        loadingReports: false
      });
    }

    case GET_SUCCESS('regex'):
    {
      return state.merge({
        regexes: List(action.data)
      });
    }

    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action === 'regex_created') {
        return state.update('regexes', (regexes) => regexes.push(msg.regex));
      } else if (msg.action === 'apply_regex' && !!state.get('selectedBatchId')) {
        if (state.get('selectedBatchId') === msg.batch) {
          const report = msg.report || msg.negative_report;
          if (report) {
            return state.update('reports', (reports) => reports.push(report));
          }
        }
      } else if (msg.action === 'download_reports') {
          return state.merge({
            bulkDownloadTaskState: false,
            bulkDownloadUrl: `${window.location.origin}${msg.url}`.replace(' ', '%20')
          })
      }
      return state;
    }

    case RegExConstants.SET_MODAL_OPEN:
    {
      return state.setIn([ 'isModalOpen', action.data.modal ], action.data.isOpen)
    }

    case RegExConstants.BATCH_SELECT:
    {
      return state.merge({
        selectedBatchId: action.data,
        selectedReport: new Map(),
        loadingReports: true
      });
    }

    case RegExConstants.REPORT_SELECT:
    {
      return state.merge({
        selectedReport: state.get('reports').find(el => el.uuid === action.uuid)
       });
    }

    case RegExConstants.REGEX_SELECT:
    {
      return state.merge({ selectedRegEx: action.data });
    }

    case RegExConstants.REGEX_DESELECT:
    {
      return state.merge({ selectedRegEx: new Map() });
    }

    case RegExConstants.PROJECT_SELECT:
    {
      return state.merge({
        selectedProjectId: action.data,
        reports: new List(),
        selectedReport: new Map(),
        selectedBatchId: null
      })
    }

    case RegExConstants.BULK_DOWNLOAD_TASK_STATE:
    {
      return state.merge({
        bulkDownloadTaskState: action.data
      })
    }

    case RegExConstants.CLEAR_BULK_DOWNLOAD_URL:
    {
      return state.merge({
        bulkDownloadUrl: ''
      })
    }

    default:
    {
      return state
    }
  }
};

export default regexReducers;
