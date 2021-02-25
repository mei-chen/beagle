import React from 'react';
import { render } from 'react-dom';
import { Provider } from 'react-redux';
import { Router, Route, Link, browserHistory, IndexRedirect } from 'react-router'

import configureStore from './store';
import Experiments from './experiments/';
import Evaluate from './evaluate/';
import Datasets from './datasets/';
import DatasetDetails from './dataset-details';
import CreateDataset from './create-dataset';
import CreateExperiment from './create-experiment';
import LabelingViews from './labeling';
import Sidebar from './base/components/Sidebar';

const { TasksView, NewTaskView, LabelingView, ExportDatasetView } = LabelingViews;

const store = configureStore();

const router = (
  <Router history={browserHistory}>
    <Route path="/" component={ Sidebar }>
      <IndexRedirect to="/experiments" />
      <Route path="experiments" component={ Experiments }/>
      <Route path="experiments/:id/evaluate" component={ Evaluate }/>
      <Route path="datasets" component={ Datasets }/>
      <Route path="datasets/:id/page/:page" component={ DatasetDetails }/>
      <Route path="create-dataset" component={ CreateDataset }/>
      <Route path="create-experiment" component={ CreateExperiment }/>
      <Route path="experiments/:id/edit" component={ CreateExperiment }/>
      <Route path="tasks" component={ TasksView }/>
      <Route path="create-task" component={ NewTaskView }/>
      <Route path="assignments/:id" component={ LabelingView }/>
      <Route path="export-supervised-dataset/:id" component={ ExportDatasetView }/>
    </Route>
  </Router>
)

render(
  <Provider store={store}>
    { router }
  </Provider>,

  document.getElementById('app')
);
