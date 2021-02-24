import React, { Component, PropTypes } from 'react';
import { List, Map, toJS } from 'immutable';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { browserHistory } from 'react-router';
import { Grid, Button, Table, Alert, FormGroup, FormControl, Modal, ModalHeader, ModalBody } from 'react-bootstrap';
import Truncate from 'base/components/Truncate';
import InCollaborationIcon from 'base/components/InCollaborationIcon';
import FilterableSelect from 'base/components/FilterableSelect';
import PreviewTable from 'base/components/PreviewTable';
import AssignUsers from 'labeling/components/AssignUsers';
import InfoIcon from 'base/components/InfoIcon';
import LabelingTable from 'labeling/components/LabelingTable';

import { getFromServer as getDatasets } from 'datasets/redux/modules/datasets_module';
import {
  resetNewTask,
  chooseDataset,
  chooseAssignee,
  removeAssignee,
  postToServer as createTask,
  getPreviewFromServer as getPreview,
  getSamplesFromServer as getSamples,
  changeSampleOnServer as changeSample,
  setLabel,
  resetLabels,
  EVALUATE_SAMPLES_SIZE
} from 'labeling/redux/modules/tasks_module';

const EVALUATED_SAMPLES_MIN = 5;

class NewTaskView extends Component {
  constructor(props) {
    super(props);
    this._renderDatasetValue = this._renderDatasetValue.bind(this);
    this._renderAssignees = this._renderAssignees.bind(this);
    this._chooseDataset = this._chooseDataset.bind(this);
    this._renderSamplesStats = this._renderSamplesStats.bind(this);
    this._createTask = this._createTask.bind(this);

    this.PREVIEW_SAMPLES_SHOW = 5;

    this.state = {
      nameValue: '',
      descriptionValue: '',
      showModal: false
    }
  }

  componentWillMount() {
    const { resetNewTask, getDatasets } = this.props;
    resetNewTask();
    getDatasets();
  }

  _renderDatasetValue(dataset) {
    return (
      <span>
        <Truncate maxLength={80}>{ dataset.get('name') }</Truncate>
        { dataset.get('is_owner') === false && <InCollaborationIcon /> }
      </span>
    )
  }

  _renderAssignees(assignees) {
    const { removeAssignee } = this.props;

    if(assignees.size > 5) return <span>{ `${assignees.size} users assigned` }</span>

    return assignees.map((assignee, i) => (
      <span
        key={i}
        className="create-task-assignee">
        { assignee.get('username') }
        <i
          className="fa fa-times-circle"
          onClick={() => removeAssignee(assignee)} />
      </span>
    ))
  }

  _renderSamplesStats(samples) {
    return (
      <div className="create-task-samples">
        { samples.filter(x => x.get('label') !== undefined).size } samples
        <span className="create-task-samples-stats">
          (
          <span>
            { samples.filter(x => x.get('label') === true).size }
            <i className="fa fa-check-circle" />
          </span>,
          <span>
            { samples.filter(x => x.get('label') === false).size }
            <i className="fa fa-minus-circle" />
          </span>
          )
        </span>
      </div>
    )
  }

  _chooseDataset(dataset) {
    const { chooseDataset, getPreview, getSamples, chooseAssignee, user } = this.props;
    chooseDataset(dataset);
    this.setState({ nameValue: dataset.get('name') })
    chooseAssignee(user); // assign user by default
    getPreview(dataset.get('id'));
    getSamples(dataset.get('id'));
  }

  _createTask() {
    const { createTask, onCreate, user, dataset, assignees, samples, chooseAssignee, removeAssignee } = this.props;
    const { nameValue, descriptionValue } = this.state;

    createTask(
      dataset.get('id'),
      user.get('id'),
      nameValue,
      descriptionValue,
      assignees.map(assignee => assignee.get('id')).toJS(),
      samples.get('data').filter(sample => sample.get('label') !== undefined).toJS()
    ).then(res => {
      browserHistory.push('/tasks');
    })
  }

  render() {
    const { user, datasets, dataset, preview, assignees, samples, setLabel, changeSample, chooseAssignee, removeAssignee } = this.props;
    const { nameValue, descriptionValue, showModal } = this.state;
    const labeledSamples = samples.get('data').filter(x => x.get('label') !== undefined);
    const canNotBeCreated = !nameValue || !descriptionValue || assignees.size === 0 || labeledSamples.size < EVALUATED_SAMPLES_MIN;
    const infoMessagesMap = {
      'Invalid name or requirements': !nameValue || !descriptionValue,
      'No users assigned': assignees.size === 0,
      [`Label at least ${EVALUATED_SAMPLES_MIN} samples`]: labeledSamples.size < EVALUATED_SAMPLES_MIN
    }

    return (
      <Grid fluid>
        <h1>Create new task</h1>
        <hr />
        <div className="create-task">
          {/* dataset select */}
          { datasets.size > 0 && !!user ? (
            <FormGroup>
              <strong className="wrap-label">Dataset:</strong>
              <div className="wrap-input">
                <FilterableSelect
                  items={datasets}
                  getter={dataset => dataset.get('name')}
                  renderer={this._renderDatasetValue}
                  onClick={this._chooseDataset}
                  placeholder="Select a dataset" />
              </div>
            </FormGroup>
          ) : (
            <div>No datasets to choose</div>
          ) }

          {/* preview loader */}
          { preview.get('isLoading') && <div className="create-task-loader"><i className="fa fa-spinner fa-spin" /> Loading samples... </div> }

          {/* preview error */}
          { preview.get('isError') && <Alert bsStyle="warning">Error while getting preview</Alert> }

          {/* preview */}
          { preview.get('data').size > 0 && (
            <div className="create-task-preview">
              <PreviewTable data={preview.get('data').slice(0, this.PREVIEW_SAMPLES_SHOW)} />
            </div>
          ) }

          {/* name & descriptions fields */}
          { !dataset.isEmpty() && (
            <div>
              <FormGroup>
                <strong className="wrap-label">Task Name:</strong>
                <div className="wrap-input">
                  <FormControl
                    type="text"
                    value={nameValue}
                    onChange={e => this.setState({ nameValue: e.target.value })} />
                </div>
              </FormGroup>
              <FormGroup>
                <strong className="wrap-label">Requirements:</strong>
                <div className="wrap-input">
                  <FormControl
                    componentClass="textarea"
                    value={descriptionValue}
                    onChange={e => this.setState({ descriptionValue: e.target.value })} />
                </div>
              </FormGroup>
            </div>
          ) }

          {/* users select */}
          { !dataset.isEmpty() && (
            <FormGroup className="create-task-select">
              <strong className="wrap-label">Assignees:</strong>
              { assignees.size > 0 && this._renderAssignees(assignees) }
              <AssignUsers
                datasetId={dataset.get('id')}
                checked={assignees}
                onCheck={user => chooseAssignee(user)}
                onUncheck={user => removeAssignee(user)} />
            </FormGroup>
          ) }

          {/* evaluation */}
          { !dataset.isEmpty() && (
            <div>
              <FormGroup>
                <strong className="wrap-label">Evaluation:</strong>
                <div className="wrap-input">
                  { this._renderSamplesStats(samples.get('data')) }
                  <Button
                    className="create-task-button"
                    bsStyle="default"
                    bsSize="small"
                    onClick={() => this.setState({ showModal: true })}>
                    <i className="fa fa-tasks" /> Set Evaluation
                  </Button>
                </div>
              </FormGroup>

              <Modal
                className="create-task-modal"
                show={showModal}
                onHide={() => this.setState({ showModal: false })}>
                <ModalHeader closeButton>
                  <h3>Label samples</h3>
                </ModalHeader>
                <ModalBody>
                  <LabelingTable
                    mode="creator"
                    samples={samples.get('data')}
                    onSet={(index, label) => setLabel(index, label)}
                    onChange={(index, sample) => changeSample(dataset.get('id'), index, sample)}
                    allowChange={dataset.get('samples') > EVALUATE_SAMPLES_SIZE} />
                </ModalBody>
              </Modal>
            </div>
          ) }

          {/* button */}
          { !dataset.isEmpty() && (
            <div>
              <Button
                bsStyle="primary"
                disabled={canNotBeCreated}
                onClick={this._createTask}>
                Create
              </Button>
              { canNotBeCreated && <InfoIcon messagesMap={infoMessagesMap} /> }
            </div>
          )}
        </div>
      </Grid>
    );
  }
}

NewTaskView.propTypes = {
  user: PropTypes.instanceOf(Map),
  datasets: PropTypes.instanceOf(List),
  dataset: PropTypes.instanceOf(Map),
  assignees: PropTypes.instanceOf(List),
  preview: PropTypes.instanceOf(Map),
  samples: PropTypes.instanceOf(Map)
}

const mapStateToProps = state => ({
  user: state.user.get('details'),
  datasets: state.datasetsModule.get('datasets'),
  dataset: state.tasksModule.get('dataset'),
  assignees: state.tasksModule.get('assignees'),
  preview: state.tasksModule.get('preview'),
  samples: state.tasksModule.get('samples')
});

const mapDispatchToProps = dispatch => (
  bindActionCreators({
    resetNewTask,
    getDatasets,
    chooseDataset,
    chooseAssignee,
    removeAssignee,
    createTask,
    getPreview,
    getSamples,
    changeSample,
    setLabel,
    resetLabels
  }, dispatch)
)

export default connect(mapStateToProps, mapDispatchToProps)(NewTaskView);
