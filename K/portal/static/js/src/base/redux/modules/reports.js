import axios from 'axios';
import { List } from 'immutable';

import { getFromServer, postToServer, patchToServer } from 'base/redux/requests';
import {
    GET_REQUEST,
    GET_SUCCESS,
    GET_ERROR,
    POST_REQUEST,
    POST_SUCCESS,
    PATCH_SUCCESS,
    POST_ERROR
} from 'base/redux/actions';

const ENDPOINT = window.CONFIG.API_URLS.reportList;
export const REGEX_TYPE = 0;
export const KEYWORD_TYPE = 1;
export const SENTENCE_TYPE = 2;

// projects request
const getReportRequest = () => {
  return {
    type: GET_REQUEST('report')
  };
};

const getReportSuccess = (data, extra) => {
  const type = (extra) ? GET_SUCCESS(extra.type) : GET_SUCCESS('report');
  const key = (extra) ? extra.key : undefined;
  return {
    type,
    key,
    data
  };
};

const getReportError = (err) => {
  return {
    type: GET_ERROR('report'),
    err
  };
};

export const getReports = (data = {}, extra) => {
  return getFromServer(
    ENDPOINT, data, getReportRequest, getReportSuccess, getReportError, extra);
};

export function getReportForBatch(batch, report_type, module_name) {
  return dispatch => {
    dispatch(getReports(
      {batch: batch, report_type: report_type}, {
        type: 'reportsForBatch' + module_name, key: 'reports'
    }));
  }
}
