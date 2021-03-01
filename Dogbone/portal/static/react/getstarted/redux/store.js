import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers
} from 'redux';
import thunk from 'redux-thunk';

// App
import user from 'common/redux/modules/user';

const rootReducer = combineReducers({
  user,
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
