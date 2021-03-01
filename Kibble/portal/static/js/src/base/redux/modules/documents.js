import { List } from 'immutable';

import { getFromServer, patchToServer } from 'base/redux/requests';
import * as baseReduxActions from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.docList;

// projects request
const getDocRequest = () => {
  return {
    type: baseReduxActions.GET_REQUEST('document')
  };
};

const getDocSuccess = (data, extra) => {
  const type = (extra) ? baseReduxActions.GET_SUCCESS(extra.type) : baseReduxActions.GET_SUCCESS('document');
  return {
    type,
    data
  };
};

const getDocError = (err) => {
  return {
    type: baseReduxActions.GET_ERROR('document'),
    err
  };
};

export const getDocs = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT, data, getDocRequest, getDocSuccess, getDocError, extra);
};

export function getDocForBatch(batch, module_name, isorigin = true) {
  return dispatch => {
    dispatch(getDocs(
      {source_file__batch: batch, isorigin}, {
        type: 'docsForBatch' + module_name
      }
    ));
  }
}


// REDUCERS
const initialState = List();


export default (state = initialState, action) => {
  switch (action.type) {

    case baseReduxActions.GET_SUCCESS('batch'):
      return List(action.data);

    case baseReduxActions.POST_SUCCESS('batch'):
      return state.push(action.response.data);

    case baseReduxActions.PATCH_SUCCESS('batch'):
      return state.map((obj) => {
        if (obj.resource_uri === action.response.resource_uri) {
          return action.response
        }
        return obj
      });

    default:
    {
      return state;
    }
  }
};
