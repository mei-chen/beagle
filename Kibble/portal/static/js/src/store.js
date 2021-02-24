import { createStore, applyMiddleware, combineReducers, compose } from 'redux';
import React from 'react'
import thunk from 'redux-thunk';
import io from 'socket.io-client';

// Project management app
import projectsReducer from 'ProjectManagement/redux/reducers';
import { MODULE_NAME as ProjectManagementName } from 'ProjectManagement/constants'

// Batch management app
import batchReducer from 'BatchManagement/redux/reducers';
import { MODULE_NAME as BatchManagementName } from 'BatchManagement/constants'

//online folder
import onlineFolder from 'OnlineFolder/redux/modules/onlineFolder'

// Message app
import { MODULE_NAME as MessageName } from 'Messages';
import MessageQueueReducer from 'Messages/reducers';
import {reducer as notifications} from 'react-notification-system-redux';
import { pushMessage } from 'Messages/actions';

import { MODULE_NAME as ProgressNotificationName } from 'ProgressNotification';
import ProgressNotificationReducer from 'ProgressNotification/reducers';
import { ProgressNotification, LogNotification } from 'ProgressNotification/components/Notify';
import { triggerProgress, triggerLog, pushLogEntry } from 'ProgressNotification/actions'

// Identifiable information app
import IdentifiableInformationReducer from 'IdentifiableInformation/redux/reducers';
import {MODULE_NAME as IdentifiableInformationName } from 'IdentifiableInformation/redux/constants';

/*
// OCR app
import ocrReducer from 'OCR/redux/reducers';
*/ // Remove for now

// Format conversion app
import FFCReducer from 'FormatConverting/redux/reducers';
import { MODULE_NAME as FFCName } from 'FormatConverting/constants'

// Cleanup Document app
import CDReducer from 'CleanupDocument/redux/reducers';
import { MODULE_NAME as CDName } from 'CleanupDocument/constants'

// SentenceSearch app
import SentencesReducers from 'SentenceSearch/redux/reducers';
import { MODULE_NAME as SentencesName } from 'SentenceSearch/constants'

// RegEx app
import RegExReducer from 'RegEx/redux/reducers';
import { MODULE_NAME as RegExName } from 'RegEx/constants'

// KeyWords app
import keywordlistReducers from 'KeyWords/redux/reducers';
import { MODULE_NAME as KeyWordsName } from 'KeyWords/constants'

import SentencesObfuscationReducers from 'SentencesObfuscation/redux/reducers';
import { MODULE_NAME as SentencesObfuscationName } from 'SentencesObfuscation/redux/constants'

// OnlineFolder app
import { reducers as OnlineFolder} from 'OnlineFolder';
import { reducers as global } from 'base';

// SentenceSplitting app
import SSReducer from 'SentenceSplitting/redux/reducers';
import { MODULE_NAME as SSName } from 'SentenceSplitting/redux/constants';

// Settings app
import settings from 'Settings/redux/modules/settings'

// Redux form
import { reducer as reduxForm } from 'redux-form'

let serverAddress;

if (window.location.hostname === 'localhost') {
  // If local bind the port
  serverAddress = `${window.location.protocol}//${window.location.hostname}:4000`;
} else {
  serverAddress = `${window.location.protocol}//${window.location.hostname}`;
}
const socket = io(serverAddress);
const reducers = combineReducers({
  [ProjectManagementName]: projectsReducer,
  [BatchManagementName]: batchReducer,
  onlineFolder:onlineFolder,
  [MessageName]: MessageQueueReducer,
  [IdentifiableInformationName]: IdentifiableInformationReducer,
  //ocrStore: ocrReducer, //Remove for now
  [FFCName]: FFCReducer,
  [CDName]: CDReducer,
  [SentencesName]: SentencesReducers,
  [RegExName]: RegExReducer,
  [KeyWordsName]: keywordlistReducers,
  [SentencesObfuscationName]: SentencesObfuscationReducers,
  form: reduxForm,
  [SSName]: SSReducer,
  [ProgressNotificationName]: ProgressNotificationReducer,
  global,
  settings:settings,
  notifications,
});

const progressNotifComponent = (
  <div>
    <ProgressNotification/>
  </div>
);

const logNotifComponent = (
  <div>
    <LogNotification/>
  </div>
)

export const socketMiddleware = (msg) => {
  return (store) => {
    msg.on('message', (resp) => {
      store.dispatch({ type: 'WEBSOCKET', data: resp });

      const triggered_progress = store.getState().ProgressNotification.get('triggered_progress');
      if (!triggered_progress && resp.message.action === 'auto_process_file_started' ) {
        store.dispatch(pushMessage(progressNotifComponent, 'info'));
        store.dispatch(triggerProgress(!triggered_progress));
      }

      const notify = resp.message.notify;
      const triggered_log = store.getState().ProgressNotification.get('triggered_log');
      if (!triggered_log && notify && Object.keys(notify).length ) {
        store.dispatch(pushMessage(logNotifComponent, 'info'));
        store.dispatch(triggerLog(!triggered_log));
      }

      if (notify && !!Object.keys(notify).length) {
        store.dispatch(pushLogEntry({message:notify.message,level:notify.level}));
      }

    });

    return next => (action) => {
      return next(action);
    };

  };
};

function reduxStore(initialState) {
  const store = createStore(
    reducers,
    initialState,
    compose(
      applyMiddleware(
        thunk,
        socketMiddleware(socket)
      ),
      window.devToolsExtension ? window.devToolsExtension() : f => f
    )
  );
  return store;
}

export default reduxStore;
