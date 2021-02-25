import TasksView from './components/TasksView';
import LabelingView from './components/LabelingView';
import NewTaskView from './components/NewTaskView';
import ExportDatasetView from './components/ExportDatasetView';
import _reducers from './redux/reducers';

export default { TasksView, NewTaskView, LabelingView, ExportDatasetView };
export const reducers = _reducers;
