import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers
} from 'redux';
import thunk from 'redux-thunk';

// Common module
import persistentnotification from 'common/redux/modules/persistentnotification';
import transientnotification from 'common/redux/modules/transientnotification';
import subscription from 'common/redux/modules/subscription';
import user from 'common/redux/modules/user';
import summary from './modules/summary';
import setting from 'account/redux/modules/setting';

const rootReducer = combineReducers({
  user,
  subscription,
  persistentnotification,
  transientnotification,
  summary,
  setting,
});

export default (initialState) => {
  return createStore(
    rootReducer,
    initialState,
    compose(
        applyMiddleware(
          thunk,
        ),
        window.devToolsExtension ? window.devToolsExtension() : f => f
    ),
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  )
}
