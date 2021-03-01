import { Map, List } from 'immutable';
import * as SentenceSearchConstants from 'SentenceSearch/redux/constants';
import { GET_REQUEST, GET_SUCCESS, POST_SUCCESS } from 'base/redux/actions';

import { MODULE_NAME } from 'SentenceSearch/constants'

const initialState = Map({
  inputSentence: '',
  selectedReport: new Map(),
  project_batches: new List(),
  reports: new List(),
  loadingReports: false,
  selectedProjectId: null,
  selectedBatchId: null,
  bulkDownloadTaskState: false,
  bulkDownloadUrl: '',
  isModalOpen: new Map({
    preview: false
  })
});

const keywordlistReducers = (state = initialState, action) => {
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

    case SentenceSearchConstants.PROJECT_SELECT:
    {
      return state.merge({
        selectedProjectId: action.data,
        selectedReport: new Map(),
        reports: new List(),
        selectedBatchId: null
      })
    }

    case SentenceSearchConstants.BATCH_SELECT:
    {
      return state.merge({
        selectedBatchId: action.data,
        selectedReport: new Map(),
        loadingReports: true
       });
    }

    case SentenceSearchConstants.REPORT_SELECT:
    {
      return state.merge({
        selectedReport: state.get('reports').find(el => el.uuid === action.uuid)
       });
    }

    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action === 'sentences'  && !!state.get('selectedBatchId')) {
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

    case SentenceSearchConstants.SET_MODAL_OPEN:
    {
      return state.setIn([ 'isModalOpen', action.data.modal ], action.data.isOpen)
    }

    case SentenceSearchConstants.CHANGE_SENTENCE_INPUT:
    {
      return state.merge({
        inputSentence: action.sentence
      })
    }

    case SentenceSearchConstants.BULK_DOWNLOAD_TASK_STATE:
    {
      return state.merge({
        bulkDownloadTaskState: action.data
      })
    }

    case SentenceSearchConstants.CLEAR_BULK_DOWNLOAD_URL:
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

export default keywordlistReducers;
