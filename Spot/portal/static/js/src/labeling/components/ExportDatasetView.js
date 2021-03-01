import React, { Component, PropTypes } from 'react';
import { Map } from 'immutable';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Link } from 'react-router';
import { Grid, FormGroup, FormControl, Button, Alert } from 'react-bootstrap';
import uuidV4 from 'uuid/v4';
import AssigneesTable from 'labeling/components/AssigneesTable';
import CustomSlider from 'base/components/Slider';
import AccordMatrix from 'labeling/components/AccordMatrix';

import {
  getTaskFromServer as getTask,
  getAccordFromServer as getAccord,
  exportDataset
} from 'labeling/redux/modules/export_dataset_module';

import {
  unassignOnServer as unassignUser
} from 'labeling/redux/modules/tasks_module';

const DEFAULT_VOTING_THRESHOLD = 80;
const DEFAULT_TRUST = 100;

class ExportDatasetView extends Component {
  constructor(props) {
    super(props);
    this._setDefaultDatasetName = this._setDefaultDatasetName.bind(this);
    this._handleThresholdChange = this._handleThresholdChange.bind(this);
    this._handleTrustChange = this._handleTrustChange.bind(this);
    this._toggleDrop = this._toggleDrop.bind(this);
    this._unassignUser = this._unassignUser.bind(this);

    this.state = {
      nameValue: '',
      descriptionValue: '',
      isAdvancedOpen: false,
      votingThreshold: DEFAULT_VOTING_THRESHOLD,
      trustById: Map()
    }
  }

  componentWillMount() {
    const { getTask } = this.props;
    const { id:taskId } = this.props.params;
    getTask(taskId)
      .then(res => this._setDefaultDatasetName(res.data.dataset.name));
  }

  _setDefaultDatasetName(name) {
    this.setState({ nameValue: `[Labeled] ${name}` });
  }

  _handleThresholdChange(value) {
    this.setState({ votingThreshold: value })
  }

  _handleTrustChange(assignmentId, value) {
    const { trustById } = this.state;
    this.setState({ trustById: trustById.set(assignmentId, value) })
  }

  _toggleDrop() {
    const { isAdvancedOpen } = this.state;
    const { task, getAccord } = this.props;
    const { id:taskId } = this.props.params;

    this.setState({ isAdvancedOpen: !isAdvancedOpen });

    if(!isAdvancedOpen && task.get('data').get('assignments').size > 1) getAccord(uuidV4(), taskId);
  }

  _unassignUser(assignmentId) {
    const { unassignUser, getTask, getAccord } = this.props;
    const { id:taskId } = this.props.params;
    unassignUser(taskId, assignmentId)
      .then(() => {
        getTask(taskId);
        getAccord(uuidV4(), taskId)
      });
  }

  render() {
    const { task, accord, exporting, exportDataset } = this.props;
    const { id:taskId } = this.props.params;
    const { nameValue, descriptionValue, isAdvancedOpen, votingThreshold, trustById } = this.state;

    if(task.get('isLoading')) return <div className="spinner spinner--center" />;

    return (
      <Grid fluid>
        <h1 className="title">
          <Link className="link-back" to={`/tasks`}>
            <i className="fa fa-chevron-left" />
          </Link>
          <span>Export Supervised Dataset</span>
          { !task.get('data').isEmpty() && <span className="gray-label">{ task.get('data').get('name') }</span> }
        </h1>
        <hr />

        { exporting.get('isSuccess') && (
          <Alert bsStyle="success">
            Dataset saved successfully
            <Link
              className="saved-dataset-link"
              to={`/datasets/${exporting.get('data').get('id')}/page/1`}>
              <i className="fa fa-database" />
              <span>{ exporting.get('data').get('name') }</span>
            </Link>
          </Alert>
        ) }

        {/* export data */}
        { !task.get('data').isEmpty() && (
          <div className="export">
            {/* input */}
            <h3 className="export-title">Input Dataset</h3>
            <div className="export-info">
              <span className="export-info-dataset">
                <i className="fa fa-database" />
                <Link to={`/datasets/${task.get('data').get('dataset').get('id')}/page/1`}>
                  { task.get('data').get('dataset').get('name') }
                </Link>
              </span>
              <span className="export-info-size">
                Size:
                <span className="export-info-size-value">
                  <strong>{ task.get('data').get('dataset').get('samples') }</strong> rows
                </span>
              </span>
            </div>

            {/* progress */}
            <h3 className="export-title">Progress</h3>
            <div className="export-progress">
              <div className="export-assignees">
                {/* assignees table */}
                <AssigneesTable
                  taskId={+taskId}
                  assignments={task.get('data').get('assignments')}
                  trustById={trustById}
                  onRemove={this._unassignUser}
                  onTrustChange={this._handleTrustChange}
                  defaultTrust={DEFAULT_TRUST}
                  extended={isAdvancedOpen} />

                {/* advanced options */}
                { isAdvancedOpen && (
                  <div className="export-advanced-drop clearfix">

                    {/* accord matrix */}
                    { task.get('data').get('assignments').size > 1 && (
                      <div className="export-advanced-accord">
                        <h4>Accord Matrix</h4>
                        { accord.get('isLoading') && <i className="fa fa-spinner fa-spin" /> }

                        { accord.get('data').size > 0 && (
                          <AccordMatrix
                            matrix={accord.get('data')}
                            users={task.get('data').get('assignments').map(assignment => assignment.getIn(['assignee', 'username']))} />
                        ) }
                      </div>
                    ) }

                    {/* voting threshold */}
                    <h5>Voting threshold:</h5>
                    <CustomSlider
                      sliderPercentage={votingThreshold}
                      handleSliderChange={this._handleThresholdChange}
                      infoMessage="Specify the voting threshold" />
                  </div>
                ) }
              </div>

              { /* advanced options toggle */ }
              <span
                className="toggle-link export-advanced-toggle"
                onClick={this._toggleDrop}>
                { isAdvancedOpen ? <i className="fa fa-chevron-double-up" /> : <i className="fa fa-chevron-double-down" /> }
                Advanced
              </span>
            </div>

            {/* output */}
            <h3 className="export-title">Output Dataset</h3>
            <div className="export-output">
              <FormGroup>
                <strong className="wrap-label">Name:</strong>
                <div className="wrap-input">
                  <FormControl
                    type="text"
                    value={nameValue}
                    onChange={e => this.setState({ nameValue: e.target.value })} />
                </div>
              </FormGroup>
              <FormGroup>
                <strong className="wrap-label">Description:</strong>
                <div className="wrap-input">
                  <FormControl
                    componentClass="textarea"
                    value={descriptionValue}
                    onChange={e => this.setState({ descriptionValue: e.target.value })} />
                </div>
              </FormGroup>
              <hr />
              <Button
                bsStyle="success"
                onClick={() => exportDataset(uuidV4(), taskId, nameValue, descriptionValue, votingThreshold)}
                disabled={exporting.get('isLoading')}>
                Save { exporting.get('isLoading') && <i className="fa fa-spinner fa-spin" /> }
              </Button>
            </div>
          </div>
        ) }
      </Grid>
    )
  }
}

ExportDatasetView.propTypes = {
  task: PropTypes.instanceOf(Map).isRequired,
  accord: PropTypes.instanceOf(Map).isRequired,
  exporting: PropTypes.instanceOf(Map).isRequired,
};

const mapStateToProps = state => ({
  task: state.exportDatasetModule.get('task'),
  accord: state.exportDatasetModule.get('accord'),
  exporting: state.exportDatasetModule.get('exporting')
});

const mapDispatchToProps = dispatch => (
  bindActionCreators({
    getTask,
    getAccord,
    unassignUser,
    exportDataset
  }, dispatch)
);

export default connect(mapStateToProps, mapDispatchToProps)(ExportDatasetView);
