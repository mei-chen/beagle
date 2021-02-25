import { createStore, applyMiddleware, combineReducers, compose } from 'redux';
import thunk from 'redux-thunk';
import io from 'socket.io-client';
import { browserHistory } from 'react-router';

// App
import { reducers as terry }  from 'search';
import { reducers as history }  from 'reports-history';
import { reducers as settings }  from 'settings';
import { reducers as user } from 'base';
import { reducers as permalink } from 'permalink';
import { setPackageManager } from 'search/redux/modules/terry';
import { getFromServer as getUserFromServer } from 'base/redux/modules/user';

let serverAddress;

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  // If local bind the port
  serverAddress = `${window.location.protocol}//${window.location.hostname}:4000`;
} else {
  serverAddress = `${window.location.protocol}//${window.location.hostname}`;
}

const socket = io(serverAddress);
const reducers = combineReducers({
  terry,
  history,
  settings,
  user,
  permalink
});

export const socketMiddleware = (socket) => {
  return ({ dispatch, getState }) => {
    socket.on('message', resp => {
      const taskUuid = getState().terry.get('taskUuid');

      if (resp.message.type === 'license_report') {
        // if this task was run in different window: do nothing
        if(resp.message.task_uuid !== taskUuid) return false;

        browserHistory.push(`/report/${resp.message.uuid}`);

        // update user data (reports_public_count, reports_private_count)
        dispatch(getUserFromServer())
      }

      if (resp.message.type === 'progress') {
        // if this task was run in different window: do nothing
        if(resp.message.task_uuid !== taskUuid) return false;

        dispatch(setPackageManager(resp.message.package_manager));
      }
    });

    return next => action => {
      return next(action);
    }
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
