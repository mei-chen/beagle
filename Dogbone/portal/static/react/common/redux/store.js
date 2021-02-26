import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers
} from 'redux';
import thunk from 'redux-thunk';

// App
import user from 'common/redux/modules/user';
import persistentnotification from 'common/redux/modules/persistentnotification';
import transientnotification from 'common/redux/modules/transientnotification';
import subscription from 'common/redux/modules/subscription';
import annotations from 'common/redux/modules/annotations';
import viewed_by from 'common/redux/modules/viewed_by';

const rootReducer = combineReducers({
  user,
  subscription,
  annotations,
  persistentnotification,
  transientnotification,
  viewed_by
});

export default (initialState) => {
  return createStore(
    rootReducer,
    initialState,
    compose(
      applyMiddleware(thunk),
      window.devToolsExtension ? window.devToolsExtension() : f => f
    ),
  )
}
