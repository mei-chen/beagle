import { List } from 'immutable';
import * as messagesConstants from 'Messages/constants';


const initialState = List();

export default (state = initialState, action) => {
  switch (action.type) {
    case messagesConstants.PUSH_MESSAGE:
      const level = action.level || 'info';
      const message = action.message || 'info';

      return state.push({level, message});

    case messagesConstants.CLEAR_MESSAGES:
      return initialState;

    case messagesConstants.DISMISS_MESSAGE:
      return state.filter(msg => msg.message.uid !== action.uid);

    default:
      return state;
  }
};
