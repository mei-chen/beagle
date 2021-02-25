import React from 'react';
import { render } from 'react-dom';
import { Provider } from 'react-redux';
import { Router, Route, browserHistory, IndexRedirect } from 'react-router';

import configureStore from '../store';
import terry from 'search';
import ReportPage from 'search/components/ReportPage';
import history from 'reports-history';
import settings from 'settings';
import Sidebar from 'base/components/Sidebar';

const store = configureStore();

const router = (
  <Router history={browserHistory}>
    <Route path="/" component={Sidebar}>
      <IndexRedirect to="/dashboard" />
      <Route path="dashboard" component={terry}/>
      <Route path="report/:uuid" component={ReportPage}/>
      <Route path="history/:page" component={history}/>
      <Route path="settings" component={settings}/>
    </Route>
  </Router>
);

render(
  <Provider store={store}>
    { router }
  </Provider>,

  document.getElementById('app')
);
