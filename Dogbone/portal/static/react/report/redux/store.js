import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers
} from 'redux';
import thunk from 'redux-thunk';
import io from 'socket.io-client';

// Common module
import persistentnotification from 'common/redux/modules/persistentnotification';
import transientnotification from 'common/redux/modules/transientnotification';
import subscription from 'common/redux/modules/subscription';
import user from 'common/redux/modules/user';
import annotations from 'common/redux/modules/annotations';
import viewed_by from 'common/redux/modules/viewed_by';

// Account module
import keyword from 'account/redux/modules/keyword';
import learner from 'account/redux/modules/learner';

// report module
import { socketMiddleware as reportSocketMiddleware } from 'report/redux/middleware';
import { socketMiddleware as commonSocketMiddleware } from 'common/redux/middleware';

import clausestatistic from 'report/redux/modules/clausestatistic';
import report from 'report/redux/modules/report';
import app from 'report/redux/modules/app';


const socket = io(window.socketServerAddr);

const rootReducer = combineReducers({
  user,
  subscription,
  annotations,
  persistentnotification,
  transientnotification,
  report,
  app,
  keyword,
  learner,
  clausestatistic,
  viewed_by
});

export default (initialState) => {
  return createStore(
    rootReducer,
    initialState,
    compose(
        applyMiddleware(
          thunk,
          reportSocketMiddleware(socket),
          commonSocketMiddleware(socket)
        ),
        window.devToolsExtension ? window.devToolsExtension() : f => f
    ),
  )
}
