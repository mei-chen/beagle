import axios from 'axios';
import { toJSON } from 'immutable';

// CONSTANTS
import * as FormatConvertingReduxConstants from 'FormatConverting/redux/constants';

// ACTION'S GENERATOR
const filterUpdateGen = (value) => {
  return {
    type: FormatConvertingReduxConstants.FILTER_UPDATE,
    value
  }
};

const checkFileGen = (uri, checked) => {
  return {
    type: FormatConvertingReduxConstants.CHECK_FILE,
    uri, checked
  }
};

export function updateFilter(value) {
  return dispatch => dispatch(filterUpdateGen(value))
}

export function setState(file, checked) {
  return dispatch => dispatch(checkFileGen(file, checked))
}
