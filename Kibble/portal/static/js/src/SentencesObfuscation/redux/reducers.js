import { Map, List } from 'immutable';
import * as SentencesObfuscationConstants from 'SentencesObfuscation/redux/constants';
import { MODULE_NAME  } from 'SentencesObfuscation/redux/constants';

import {
  REGEX_TYPE,
  KEYWORD_TYPE,
  SENTENCE_TYPE
} from 'base/redux/modules/reports';


const initialState = Map({
  batches: new List(),
  sentences_reports: new List(),
  keywords_reports: new List(),
  regex_reports: new List(),
  selected_reports: new List(),
  selceted_sentences: new Map({}),
  isModalOpen: false,
  show_downloads: false,
  loading_downloads: false,
  docs: new List()
});
export default (state = initialState, action) => {
  switch (action.type) {

    case `batchForProject/${MODULE_NAME}/GET_SUCCESS`:
    {
      return state.merge({
        batches: List(action.data)
      });
    }

    case `reportsForBatch${SENTENCE_TYPE}/${MODULE_NAME}/GET_SUCCESS`:
    {
      return state.merge({
        sentences_reports: List(action.data)
      });
    }

    case `reportsForBatch${KEYWORD_TYPE}/${MODULE_NAME}/GET_SUCCESS`:
    {
      return state.merge({
        keywords_reports: List(action.data)
      });
    }

    case `reportsForBatch${REGEX_TYPE}/${MODULE_NAME}/GET_SUCCESS`:
    {
      return state.merge({
        regex_reports: List(action.data)
      });
    }

    case SentencesObfuscationConstants.RESET_REPORTS_LISTS:
    {
      return state.merge({
        sentences_reports: new List(),
        keywords_reports: new List(),
        regex_reports: new List(),
        selected_reports: new List()
      });
    }

    case SentencesObfuscationConstants.SELECT_REPORT:
    {
      return state.update('selected_reports', (selected_reports) => selected_reports.push(action.id));
    }

    case SentencesObfuscationConstants.UNSELECT_REPORT:
    {
      const index = state.get('selected_reports').indexOf(action.id);
      return state.update('selected_reports', (selected_reports) => selected_reports.splice(index,1));
    }

    case SentencesObfuscationConstants.SET_MODAL_OPEN:
    {
      return state.merge({
        isModalOpen: action.state
      })
    }

    case SentencesObfuscationConstants.MARK_SENTENCE:
    {
      return state.setIn(['selceted_sentences',action.rep_id,action.sent_idx],action.method);
    }

    case SentencesObfuscationConstants.MARK_ALL_SENTENCES:
    {
      return state.merge({
        'selceted_sentences': new Map(action.data)
      })
    }

    case SentencesObfuscationConstants.CANCEL_LABELING:
    {
      return state.merge({
        selceted_sentences: new Map({}),
        show_downloads: false
      })
    }

    case SentencesObfuscationConstants.DONE_LABELING:
    {
      return state.merge({
        show_downloads: true
      })
    }

    case SentencesObfuscationConstants.DOCS_SUCCESS:
    {
      return state.merge({
        loading_downloads: false,
        docs: new List(action.data)
      })
    }

    case SentencesObfuscationConstants.DOCS_REQ:
    {
      return state.merge({
        docs: new List(),
        loading_downloads: true
      })
    }

    default:
    {
      return state
    }
  }
}
