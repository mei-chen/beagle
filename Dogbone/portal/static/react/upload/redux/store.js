import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers
} from 'redux';
import thunk from 'redux-thunk';

// App
import persistentnotification from 'common/redux/modules/persistentnotification';
import transientnotification from 'common/redux/modules/transientnotification';
import subscription from 'common/redux/modules/subscription';
import user from 'common/redux/modules/user';
import setting from 'account/redux/modules/setting';
import upload from './modules/upload';

const rootReducer = combineReducers({
  user,
  upload,
  subscription,
  persistentnotification,
  transientnotification,
  setting
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
