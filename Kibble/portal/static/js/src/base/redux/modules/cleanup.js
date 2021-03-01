import { postToServer } from 'base/redux/requests';
import * as baseReduxActions from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.cleanupDocApi;

const postCleanupRequest = () => {
  return {
    type: baseReduxActions.POST_REQUEST('cleanup')
  };
};

const postCleanupSuccess = (data) => {
  return {
    type: baseReduxActions.POST_SUCCESS('cleanup'),
    data
  };
};

const postCleanupError = (err) => {
  return {
    type: baseReduxActions.POST_ERROR('cleanup'),
    err
  };
};


export const postCleanup = (data, successEvent = postCleanupSuccess,
                            errorEvent = postCleanupError) => {
  return postToServer({
    endpoint: ENDPOINT,
    data,
    successEvent,
    errorEvent,
    processEvent: postCleanupRequest
  });
};
