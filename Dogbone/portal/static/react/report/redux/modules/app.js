// This module manages the internal states of the app that'
// shared accross different components
import { Map } from 'immutable';

// Aoo
import { MODULE_NAME } from 'common/utils/constants';

const CURRENT_NAME = 'app';

const SET_FOCUS_SENTENCE = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/SET_FOCUS_SENTENCE`;
const REMOVE_FOCUS_SENTENCE = `dogbone/${MODULE_NAME}/${CURRENT_NAME}/REMOVE_FOCUS_SENTENCE`;


export const setFocusSentence = (idx) => {
  return {
    type: SET_FOCUS_SENTENCE,
    idx
  }
}

export const removeFocusSentence = (idx) => {
  return {
    type: REMOVE_FOCUS_SENTENCE,
    idx
  }
}

const initialState = Map({
  // Database Sentence
  focusedSentenceIdx: null
});

export default (state=initialState, action={}) => {
  switch (action.type) {
  case SET_FOCUS_SENTENCE: {
    return state.merge({
      focusedSentenceIdx: action.idx
    });
  }

  case REMOVE_FOCUS_SENTENCE: {
    return state.merge({
      focusedSentenceIdx: null
    });
  }

  default: {
    return state
  }
  }
}
