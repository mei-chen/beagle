import { Map, List } from 'immutable';
import * as CleanupDocumentConstants from 'CleanupDocument/redux/constants';
import { GET_REQUEST, GET_SUCCESS } from 'base/redux/actions';
import { MODULE_NAME } from 'CleanupDocument/constants';
import { updateEntry } from 'base/utils/misc'


const initialState = Map({
  project_batches: new List(),
  tools: new List(),            // List of available cleanup tools
  docs: new List(),
  blockedDocs: new List(),
  docState: new Map(),
  toolsState: new List(),
  toolsCount: 0,
  docFilterValue: ''
});

const cleanupDocReducer = (state = initialState, action) => {
  switch (action.type) {
    // REQUEST SUCCESS CASES
    case GET_SUCCESS('batchForProject' + MODULE_NAME):
    {
      return state.merge({
        project_batches: List(action.data)
      })
    }

    case GET_SUCCESS('cleanupdoctool'):
    {
      return state.merge({
        tools: List(action.data),
        toolsState: List(),
        toolsCount: action.data.length
      })
    }

    case GET_SUCCESS('docsForBatch' + MODULE_NAME):
    {
      return state.merge({
        docs: List(action.data),
        blockedDocs: List(),
      })
    }


    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action !== 'cleanup_document') {
        return state;
      }
      return state
        .setIn([ 'docState', msg.doc.id ], false)
        .merge({
          docs: updateEntry(state.get('docs'), msg.doc, (obj) => obj.id === msg.doc.id),
          blockedDocs: state.get('blockedDocs').filter(x => x !== msg.doc.id),
        });
    }

    case CleanupDocumentConstants.FILTER_UPDATE:
    {
      return state.merge({
        docFilterValue: action.value
      });
    }

    case CleanupDocumentConstants.BLOCK_DOCUMENT:
    {
      return state.merge({
        blockedDocs: List(action.doc_ids.map(item => parseInt(item)))
      });
    }

    case CleanupDocumentConstants.CHECK_FILE:
    {
      return state.setIn([ 'docState', action.uri ], action.checked);
    }

    case CleanupDocumentConstants.MANAGE_DRAG:
    {
      const { tool } = action;
      return state.merge({
        toolsState: state.get('toolsState').filter(x => x.tool !== tool.tool),
        tools: state.get('tools').filter(x => x.tool !== tool.tool)
      });
    }

    case CleanupDocumentConstants.MANAGE_DROP:
    {
      const { tool, to_selected } = action;
      if (to_selected) {
        return state.merge({
          toolsState: state.get('toolsState').push(tool),
          tools: state.get('tools').filter(x => x.tool !== tool.tool)
        });
      } else {
        return state.merge({
          tools: state.get('tools').push(tool),
          toolsState: state.get('toolsState').filter(x => x.tool !== tool.tool)
        });
      }
    }

    default:
      return state
  }
};

export default cleanupDocReducer;
