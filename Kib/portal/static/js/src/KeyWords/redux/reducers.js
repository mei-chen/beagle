import { Map, List } from 'immutable';
import * as KeywordListConstants from 'KeyWords/redux/constants';
import { GET_REQUEST, GET_SUCCESS, POST_SUCCESS } from 'base/redux/actions';

import { MODULE_NAME } from 'KeyWords/constants'

const initialState = Map({
  recommendations: new List(),
  manualkeywords: new List(),
  synonyms: new List(),
  keywordlists: new List(),
  currentWord: '',
  selectedKeywordList: new Map(),
  simmodels: new List(),
  selectedSimModel: new Map(),
  selectedReport: new Map(),
  project_batches: new List(),
  reports: new List(),
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
  }),
  excludePersonal: false
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

    case KeywordListConstants.PROJECT_SELECT:
    {
      return state.merge({
        selectedProjectId: action.data,
        selectedReport: new Map(),
        reports: new List(),
        selectedBatchId: null
      })
    }

    case KeywordListConstants.BATCH_SELECT:
    {
      return state.merge({
        selectedBatchId: action.data,
        selectedReport: new Map(),
        loadingReports: true
       });
    }

    case KeywordListConstants.REPORT_SELECT:
    {
      return state.merge({
        selectedReport: state.get('reports').find(el => el.uuid === action.uuid)
       });
    }

    case GET_SUCCESS('keywordlist'):
    {
        return state.merge({keywordlists: List(action.data)});
    }
    case POST_SUCCESS('keywordlist'):
    {
        return state.update('keywordlists', (keywordlists) => keywordlists.push(action.data));
    }

    case KeywordListConstants.INPUT_WORD:
    {
      return state.merge({currentWord: action.word});
    }

    case GET_SUCCESS('simmodel'):
    {
        return state.merge({
            simmodels: List(action.data),
        });
    }

    case KeywordListConstants.MARK_RECOMMENDATION:
    {
        return state.updateIn([ 'recommendations', action.index ], keyword => {
          const status = keyword.status === 'success' ? 'danger' : 'success';
          return { ...keyword, status }
        })
    }

    case KeywordListConstants.MARK_SYNONYM:
    {
      return state.updateIn([ 'synonyms', action.index ], keyword => {
        const status = keyword.status === 'success' ? 'danger' : 'success';
        return { ...keyword, status }
      })
    }

    case KeywordListConstants.MARK_MANUAL:
    {
      return state.updateIn([ 'manualkeywords', action.index ], keyword => {
        const status = keyword.status === 'success' ? 'danger' : 'success';
        return { ...keyword, status }
      })
    }

    case KeywordListConstants.PURGE:
    {
        return state.merge({
            recommendations: new List(),
            manualkeywords: new List()
        });
    }

    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action === 'keywordlist_created') {
          return state.merge({
              keywordlists: state.update('keywordlists', (kwls) => kwls.push(msg.keywordlist)),
          });
      } else if (msg.action === 'recommend') {
          return state.merge({
            recommendations: List( msg.keywords.map(keyword => ({ text: keyword, status: 'danger' })))
          });
      } else if (msg.action === 'synonyms') {
          return state.merge({
            synonyms: List( msg.keywords.map(keyword => ({ text: keyword, status: 'danger' })))
          });
      } else if (msg.action === 'keywordlist_search'  && !!state.get('selectedBatchId')) {
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

    case KeywordListConstants.SET_MODAL_OPEN:
    {
      if (action.data.modal === 'create') {
          let newstate = state.merge({ selectedKeywordList: new Map() });
          return newstate.setIn([ 'isModalOpen', action.data.modal ], action.data.isOpen);
      }
      return state.setIn([ 'isModalOpen', action.data.modal ], action.data.isOpen)
    }

    case KeywordListConstants.KEYWORDLIST_SELECT:
    {
      if (action.data) {
        return state.merge({ selectedKeywordList: state.get('keywordlists').find(el => el.name === action.data.value) });
      }
      return state.merge({ selectedKeywordList: new Map() });
    }

    case KeywordListConstants.KEYWORDLIST_DESELECT:
    {
      return state.merge({ selectedKeywordList: new Map() });
    }

    case KeywordListConstants.SELECT_SIMMODEL:
    {
      if (action.data) {
        return state.merge({ selectedSimModel: state.get('simmodels').find(el => el.api_name === action.data.value) });
      }
      return state.merge({ selectedSimModel: new Map() });
    }

    case KeywordListConstants.BULK_DOWNLOAD_TASK_STATE:
    {
      return state.merge({
        bulkDownloadTaskState: action.data
      })
    }

    case KeywordListConstants.CLEAR_BULK_DOWNLOAD_URL:
    {
      return state.merge({
        bulkDownloadUrl: ''
      })
    }

    case KeywordListConstants.KEYWORD_ADD:
    {
        return state.update('manualkeywords', keywords => keywords.push({ text: action.word, status: 'success' }));
    }

    case KeywordListConstants.CHANGE_EXCLUDE:
    {
        const checked = !state.get('excludePersonal');
        return state.merge({
          excludePersonal: checked
        })   
    }

    default:
    {
      return state
    }
  }
};

export default keywordlistReducers;
