import { getFromServer, postToServer, patchToServer } from 'base/redux/requests';
import * as actions from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.simmodel;

// tools request
const getSimModelsRequest = () => {
  return {
    type: actions.GET_REQUEST('simmodel')
  };
};

const getSimModelsSuccess = (data, extra) => {
  const type = (extra) ? actions.GET_SUCCESS(extra.type) : actions.GET_SUCCESS('simmodel');
  return {
    type,
    data
  };
};

const getSimModelsError = (err) => {
  return {
    type: actions.GET_ERROR('simmodel'),
    err
  };
};

export const getSimModels = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT, data, getSimModelsRequest, getSimModelsSuccess, getSimModelsError, extra);
};
