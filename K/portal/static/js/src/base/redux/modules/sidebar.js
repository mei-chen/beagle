import { Map } from 'immutable';

const SET_ACTIVE_ROOT_FOLDER = 'SIDEBAR/SET_ACTIVE_ROOT_FOLDER';
const SET_ACTIVE_URL = 'SIDEBAR/SET_ACTIVE_URL';


export const setActiveRootFolder = (data) => ({
  type: SET_ACTIVE_ROOT_FOLDER,
  data
});


export const setActiveUrl = (data) => ({
  type: SET_ACTIVE_URL,
  data
});


const initialState = Map({
  activeRootFolder: '',
  activeUrl: ''
});

export default (state = initialState, action) => {
  switch (action.type) {
    case SET_ACTIVE_ROOT_FOLDER:
    {
      return state.merge({
        activeRootFolder: action.data
      })
    }
    case SET_ACTIVE_URL:
    {
      return state.merge({ activeUrl: action.data })
    }
    default:
    {
      return state
    }
  }
}
