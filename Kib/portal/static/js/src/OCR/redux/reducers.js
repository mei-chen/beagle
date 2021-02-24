import { Map, List } from 'immutable';
import * as ocrConstants from 'OCR/redux/constants';
import { transferTo } from 'base/utils/misc';


function splitFilesByNeedOCR(data) {
  const processedFiles = data.filter(file => !file.need_ocr);
  const unprocessedFiles = data.filter(file => file.need_ocr);
  return { processedFiles, unprocessedFiles }
}


const initialState = Map({
  taskState: null, // null just initial, true Task is in progress, false Task is done
  files: new List(),
  processedFiles: new List(),
  unprocessedFiles: new List(),
  processingFiles: new List(),
  batches: new List(),
  alert: new Map(),
  reloadBatchRules: new Map({
    need: false,  // When true data will be pulled from uri below
    from: '',  // batch-detail resource uri
    type: ''  // create or update. Create pushes new Batch into batches, Update updates a batch
  })
});
export default (state = initialState, action) => {
  switch (action.type) {
    case 'WEBSOCKET':
    {
      const msg = action.data.message;
      if (msg.action !== 'ocr_file') {
        return state;
      } else if (msg.action == 'ocr_file' && msg.alert) {
        return state.set('alert', Map(msg.alert))
      } else if (msg.realize_files) {
        return state.merge({
          taskState: false,
          processingFiles: state.get('processingFiles').clear()
        })
      }
      return state.merge({
        taskState: false,
        reloadBatchRules: Map({ need: true, from: msg.resource_uri, type: msg.store_action }),
        processingFiles: state.get('processingFiles').clear(),
        alert: state.getIn(['alert', 'level']) !== 'success' ? state.get('alert') : state.get('alert').clear()
      })
    }

    case ocrConstants.UPDATE_BATCH:
    {
      const data = action.payload;
      const { processedFiles, unprocessedFiles } = splitFilesByNeedOCR(data.files);
      return state
        .update('batches', (batches) => batches.map(batch => {
          if (batch.id === data.id) return data;
          return batch
        }))
        .merge({
          files: List(data.files),
          processedFiles: List(processedFiles),
          unprocessedFiles: List(unprocessedFiles),
          reloadBatchRules: Map({ need: false, from: '', type: '' })
        })
    }

    case ocrConstants.INSERT_BATCH:
    {
      const data = action.payload;
      return state
        .update('batches', (batches) => batches.push(data))
        .merge({
          files: List(data.files),
          reloadBatchRules: Map({ need: false, from: '', type: '' })
        })
    }

    case ocrConstants.TASK_STATE:
    {
      return state.merge({
        taskState: action.value
      });
    }

    case ocrConstants.ADD_PROCESSING_FILES:
    {
      const processingFiles = state.get('processingFiles').concat(action.payload);
      return state.merge({ processingFiles })
    }

    case ocrConstants.CLEAR_PROCESSING_FILES:
    {
      return state.merge({
        processingFiles: state.get('processingFiles').clear()
      })
    }

    case ocrConstants.CLEAR_ALERT:
    {
      return state.merge({
        alert: state.get('alert').clear()
      })
    }

    case 'filesForBatch/ocr/GET_SUCCESS':
    {
      const files = action.data;
      const { processedFiles, unprocessedFiles } = splitFilesByNeedOCR(files);
      return state.merge({
        files: List(files),
        processedFiles: List(processedFiles),
        unprocessedFiles: List(unprocessedFiles)
      });
    }

    case 'batchForProject/ocr/GET_SUCCESS':
    {
      return state.merge({
        batches: List(action.data)
      });
    }

    default:
    {
      return state
    }
  }
}
