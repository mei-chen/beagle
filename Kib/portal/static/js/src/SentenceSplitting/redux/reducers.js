import { Map, List } from 'immutable';
import {
  SSAPI_POST,
  CLEAR_WS_MESSAGE,
  BULK_DOWNLOAD_TASK_STATE,
  CLEAR_BULK_DOWNLOAD_URL
} from 'SentenceSplitting/redux/constants';
import { transferTo } from 'base/utils/misc';

const initialState = Map({
  batches: new List(),
  documents: new List(),
  hasSentences: new List(),
  // When the document sent to API it goes here
  // and stays here until it not processed.
  // list holds uuids of the documents from `documents` list above
  lockedDocuments: new List(),
  wsMessage: '',
  bulkDownloadTaskState: false,
  bulkDownloadUrl: ''
});
export default (state = initialState, action) => {
  switch (action.type) {
    case 'batchForProject/SS/GET_SUCCESS':
    {
      return state.merge({
        batches: List(action.data)
      })
    }

    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action === 'sentence_splitting') {
        let newState = {
          lockedDocuments: state.get('lockedDocuments').filter(
            el => el !== msg.doc.id
          )
        };
        if (!msg.success) {
          return state.merge(newState);
        }

        let [ documents, hasSentences ] = transferTo(
          state.get('documents'), state.get('hasSentences'),
          doc_el => doc_el.id !== msg.doc.id
        );
        return state.merge({
          ...newState,
          documents,
          hasSentences,
        });
      } else if (msg.action === 'download_sentences') {
        let newState = { bulkDownloadTaskState: false };
        if (msg.success) {
          newState.bulkDownloadUrl = `${window.location.origin}${msg.url}`.replace(' ', '%20');
        }
        return state.merge(newState);
      } else return state
    }

    case 'docsForBatch/SS/GET_SUCCESS':
    {
      let documents = [];
      let hasSentences = [];
      for (const doc of action.data) {
        if (doc.has_sentences) {
          hasSentences.push(doc)
        } else {
          documents.push(doc)
        }
      }
      return state.merge({
        hasSentences: List(hasSentences),
        documents: List(documents)
      })
    }

    case SSAPI_POST:
    {
      return state.merge({
        lockedDocuments: state.get('lockedDocuments').concat(action.data)
      })
    }

    case CLEAR_WS_MESSAGE:
    {
      return state.merge({
        wsMessage: ''
      })
    }

    case BULK_DOWNLOAD_TASK_STATE:
    {
      return state.merge({
        bulkDownloadTaskState: action.data
      })
    }

    case CLEAR_BULK_DOWNLOAD_URL:
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
}
