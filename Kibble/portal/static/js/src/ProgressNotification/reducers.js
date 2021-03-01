import { Map, List } from 'immutable';
import * as messagesConstants from 'ProgressNotification/constants';


const initialState = new Map({
  initialized: false,
  max: 0,
  current: 0,
  failed: 0,
  triggered_progress: false,
  triggered_log: false,
  new_log_marker: false,
  log_list: new List()
});

export default (state = initialState, action) => {
  switch (action.type) {
    case 'WEBSOCKET':
    {
      if(action.data.message.action === 'auto_process_file_started') {
        return state.merge({
          initialized: true,
          max: action.data.message.total_files,
        })
      }
      else if(action.data.message.action === 'auto_process_file_finished') {
       return state.merge({
          current: action.data.message.files_succeeded,
          failed: action.data.message.files_failed
        })
      }
      else return state
    }

    case messagesConstants.TRIGGER_PROGRESS:
    {
      return state.merge({
        triggered_progress: action.triggered_prog
      })
    }

    case messagesConstants.TRIGGER_LOG:
    {
      return state.merge({
        new_log_marker: false,
        triggered_log: action.triggered
      })
    }

    case messagesConstants.PUSH_LOG:
    {
      return state.merge({
        new_log_marker: true,
        log_list: state.get("log_list").push(action.entry)
      })
    }

    default:
      return state;
  }
};
