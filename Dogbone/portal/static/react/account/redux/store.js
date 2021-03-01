import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers
} from 'redux';
import thunk from 'redux-thunk';
import io from 'socket.io-client';

// App
import user from 'common/redux/modules/user';
import subscription from 'common/redux/modules/subscription';
import annotations from 'common/redux/modules/annotations';
import persistentnotification from 'common/redux/modules/persistentnotification';
import transientnotification from 'common/redux/modules/transientnotification';
import viewed_by from 'common/redux/modules/viewed_by';
import project from 'account/redux/modules/project';
import setting from 'account/redux/modules/setting';
import keyword from 'account/redux/modules/keyword';
import learner from 'account/redux/modules/learner';
import experiment from 'account/redux/modules/experiment';

// Account Module
import { socketMiddleware as accountSocketMiddleware } from 'account/redux/middleware';

const rootReducer = combineReducers({
  user,
  subscription,
  annotations,
  persistentnotification,
  transientnotification,
  project,
  setting,
  keyword,
  learner,
  experiment,
  viewed_by
});

const socket = io(window.socketServerAddr);

export default (initialState) => {
  return createStore(
    rootReducer,
    initialState,
    compose(
      applyMiddleware(
        thunk,
        accountSocketMiddleware(socket)
      ),
      window.devToolsExtension ? window.devToolsExtension() : f => f
    ),
  )
}
