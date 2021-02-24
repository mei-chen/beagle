import { postToServer } from 'base/redux/requests';
import * as baseReduxActions from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.convertApi;

const postConvertRequest = () => {
  return {
    type: baseReduxActions.POST_REQUEST('convert')
  };
};

const postConvertSuccess = (data) => {
  return {
    type: baseReduxActions.POST_SUCCESS('convert'),
    data
  };
};

const postConvertError = (err) => {
  return {
    type: baseReduxActions.POST_ERROR('convert'),
    err
  };
};


export const postConvert = (files, successAction = postConvertSuccess,
                            errorAction = postConvertError) => {
  return postToServer({
    endpoint: ENDPOINT,
    data: {files},
    processEvent: postConvertRequest,
    successEvent: successAction,
    errorEvent: errorAction
  });
};
