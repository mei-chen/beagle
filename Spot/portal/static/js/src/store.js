import { createStore, applyMiddleware, combineReducers, compose } from 'redux';
import thunk from 'redux-thunk';
import io from 'socket.io-client';
import uuidV4 from 'uuid/v4';

// App
import { reducers as baseModules } from './base';
import { reducers as experimentsModule }  from './experiments';
import { reducers as evaluateModules }  from './evaluate';
import { reducers as datasetsModule }  from './datasets';
import { reducers as datasetDetailsModule }  from './dataset-details';
import { reducers as createDatasetModule } from './create-dataset';
import { reducers as createExperimentModules } from './create-experiment';
import { reducers as labelingModules } from './labeling';
import { evaluateSuccess, quitEvaluation }  from './evaluate/redux/modules/evaluate_module';
import { generateSuccess, quitGeneration }  from './evaluate/redux/modules/generate_module';
import { endTraining, quitTraining, getConfidenceSuccess, getConfidenceError }  from './create-experiment/redux/modules/create_experiment_module';
import { postSuccess as simulatePostSuccess } from './create-experiment/redux/modules/simulate_module';
import { simulateDiffSuccess } from './evaluate/redux/modules/diff_module';
import { getSamplesFromServer, getSamplesSuccess, buildExperimentSuccess } from './labeling/redux/modules/labeling_module';
import { exportDatasetSuccess, getScoresSuccess, getAccordSuccess } from './labeling/redux/modules/export_dataset_module';

const { createExperimentModule, simulateModule, onlineDbModule } = createExperimentModules;
const { previewModule, evaluateModule, generateModule, diffModule } = evaluateModules;
const { user, collaboratorsModule } = baseModules;
const { tasksModule, labelingModule, exportDatasetModule } = labelingModules;

let serverAddress;

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  // If local bind the port
  serverAddress = `${window.location.protocol}//${window.location.hostname}:4002`;
} else {
  serverAddress = `${window.location.protocol}//${window.location.hostname}`;
}

const socket = io(serverAddress);
const reducers = combineReducers({
  user,
  collaboratorsModule,
  experimentsModule,
  previewModule,
  evaluateModule,
  generateModule,
  diffModule,
  datasetsModule,
  datasetDetailsModule,
  createDatasetModule,
  createExperimentModule,
  simulateModule,
  onlineDbModule,
  tasksModule,
  labelingModule,
  exportDatasetModule
});

export const socketMiddleware = (socket) => {
  return ({ dispatch, getState }) => {
    socket.on('message', resp => {
      if(resp.message.notification === 'EXPERIMENT_EVALUATED_NOTIFICATION') {
        dispatch( evaluateSuccess(resp.message) );
      }

      if(resp.message.notification === 'EXPERIMENT_EVALUATING_ERROR_NOTIFICATION') {
        dispatch( quitEvaluation(resp.message) );
      }

      if(resp.message.notification === 'EXPERIMENT_GENERATING_ERROR_NOTIFICATION') {
        dispatch( quitGeneration(resp.message) );
      }

      if(resp.message.notification === 'EXPERIMENT_GENERATED_NOTIFICATION') {
        dispatch( generateSuccess(resp.message) );
      }

      if(resp.message.notification === 'CLASSIFIER_TRAINED_NOTIFICATION') {
        dispatch( endTraining(resp.message.clf_uuid, resp.message.scores) );
        dispatch( getConfidenceSuccess(resp.message.clf_uuid, resp.message.confidence_distribution) );
      }

      if(resp.message.notification === 'CLASSIFIER_TRAINING_ERROR_NOTIFICATION') {
        dispatch( quitTraining(resp.message.clf_uuid, resp.message.error) );
      }

      if(resp.message.notification === 'CLASSIFIER_DECISION_FUNCTION_PLOTTED_NOTIFICATION') {
        dispatch( getConfidenceSuccess(resp.message.clf_uuid, resp.message.confidence_distribution) );
      }

      if(resp.message.notification === 'CLASSIFIER_DECISION_FUNCTION_PLOTTING_ERROR_NOTIFICATION') {
        dispatch( getConfidenceError(resp.message.clf_uuid, resp.message.error) );
      }

      if(resp.message.notification === 'EXPERIMENT_SIMULATED_NOTIFICATION') {
        // task uuid of simulation in diff table starts with DIFF_SIMULATION to distinguish them from main simulation
        if(resp.message.task_uuid.indexOf('DIFF_SIMULATION') === 0) {
          dispatch( simulateDiffSuccess(resp.message) );
        } else {
          dispatch( simulatePostSuccess(resp.message) );
        }
      }

      if(resp.message.notification === 'LABELING_TASK_SAMPLES_SELECTED_NOTIFICATION') {
        dispatch( getSamplesSuccess(resp.message) );
      }

      if(resp.message.notification === 'LABELING_TASK_SAMPLES_STORED_NOTIFICATION') {
        // if 'storing samples' task (post task) was run in different window
        if(resp.message.task_uuid !== getState().labelingModule.get('postTaskUuid')) return;

        // otherwise: get new samples
        const id = getState().labelingModule.get('assignment').get('data').get('id');
        dispatch(getSamplesFromServer(uuidV4(), id))
      }

      if(resp.message.notification === 'LABELING_TASK_EXPERIMENT_BUILT_NOTIFICATION') {
        // if 'build experiment' task was run in different window
        if(resp.message.task_uuid !== getState().labelingModule.get('buildExperimentTaskUuid')) return;

        dispatch(buildExperimentSuccess(resp.message));
      }

      if(resp.message.notification === 'LABELING_TASK_SUPERVISED_DATASET_EXPORTED_NOTIFICATION') {
        // if 'export dataset' task was run in different window
        if(resp.message.task_uuid !== getState().exportDatasetModule.get('exportTaskUuid')) return;

        dispatch(exportDatasetSuccess(resp.message));
      }

      if(resp.message.notification === 'LABELING_TASK_EVALUATION_SCORE_EXPANDED_NOTIFICATION') {
        // if 'getting scores' task was run in different window
        if(resp.message.task_uuid !== getState().exportDatasetModule.get('getScoresTaskUuid')) return;

        dispatch(getScoresSuccess(resp.message));
      }

      if(resp.message.notification === 'LABELING_TASK_ACCORD_MATRIX_COMPUTED_NOTIFICATION') {
        // if 'getting accord matrix' task was run in different window
        if(resp.message.task_uuid !== getState().exportDatasetModule.get('getAccordTaskUuid')) return;

        dispatch(getAccordSuccess(resp.message));
      }
    });

    return next => action => {
      return next(action);
    }
  };
};

function reduxStore(initialState) {
  const store = createStore(
    reducers,
    initialState,
    compose(
      applyMiddleware(
        thunk,
        socketMiddleware(socket)
      ),
      window.devToolsExtension ? window.devToolsExtension() : f => f
    )
  );
  return store;
}

export default reduxStore;
