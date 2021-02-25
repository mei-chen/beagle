import React from 'react';
import { render } from 'react-dom';
import { Provider } from 'react-redux';

import configureStore from '../store';
import Permalink from 'permalink';
import Sidebar from 'base/components/Sidebar';

const store = configureStore();

render(
  <Provider store={store}>
    <Sidebar
      isHidden={true}
      isPermalink={true}>
      <Permalink />
    </Sidebar>
  </Provider>,
  document.getElementById('interface_view')
);
