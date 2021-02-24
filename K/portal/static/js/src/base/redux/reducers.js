import user from 'base/redux/modules/user';
import projects from 'base/redux/modules/projects';
import batches from 'base/redux/modules/batches';
import keywordlists from 'base/redux/modules/keywordlists';
import files from 'base/redux/modules/files';
import sidebar from 'base/redux/modules/sidebar';

import { combineReducers } from 'redux'

export default combineReducers({
  user,
  projects,
  batches,
  keywordlists,
  files,
  sidebar
})
