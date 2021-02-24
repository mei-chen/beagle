import axios from 'axios';
import Cookies from "universal-cookie";

export const sendPost = (url, data) => {
  const cookies = new Cookies();
  const axiosConf = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': cookies.get('csrftoken')
    }
  };
  return axios.post(url, data, axiosConf)
};
