import { getFromServer, postToServer, patchToServer } from 'base/redux/requests';
import * as actions from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.cleanupDocToolsApi;

// tools request
const getCleanupDocToolRequest = () => {
  return {
    type: actions.GET_REQUEST('cleanupdoctool')
  };
};

const getCleanupDocToolSuccess = (data, extra) => {
  const type = (extra) ? actions.GET_SUCCESS(extra.type) : actions.GET_SUCCESS('cleanupdoctool');
  return {
    type,
    data
  };
};

const getCleanupDocToolError = (err) => {
  return {
    type: actions.GET_ERROR('cleanupdoctool'),
    err
  };
};

export const getCleanupDocTools = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT, data, getCleanupDocToolRequest, getCleanupDocToolSuccess, getCleanupDocToolError, extra);
};
