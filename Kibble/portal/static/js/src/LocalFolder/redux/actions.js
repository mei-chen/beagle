import axios from "axios";
import { pushMessage } from "Messages/actions";
import * as baseActions from 'base/redux/actions';
import Cookies from "universal-cookie";
import {
  showFilesPopup,
  clearModalFilesList,
  multipleFileUpload
} from 'base/redux/modules/files';
const {
  batchList: batchListUri
} = window.CONFIG.API_URLS;


export function createFile(data, batch_uri) {
  return (dispatch) => {
    dispatch(clearModalFilesList());
    dispatch(showFilesPopup());
    const batch_uri = batch_uri ? batch_uri : data.batch;
    return multipleFileUpload({
      dispatch,
      key: 'content',
      values: data.content,
      inject: { batch: batch_uri }
    })
      .catch(e => dispatch(pushMessage(e, 'error')));
  }
}

export function createBatch(data) {
  return (dispatch) => {
    const cookies = new Cookies();
    const axiosConf = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': cookies.get('csrftoken')
      }
    };

    return axios.post(batchListUri, data, axiosConf)
      .then((r) => {
        data.batch = r.data.id;
        dispatch({ type: baseActions.POST_SUCCESS('batch'), data: r.data });
        dispatch(createFile(data));
      })
      .catch(console.log)
      .catch(e => dispatch(pushMessage(e, 'error')));
  }
}
