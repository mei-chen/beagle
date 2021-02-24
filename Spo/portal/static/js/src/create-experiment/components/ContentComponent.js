import React, { PropTypes } from 'react';
import { withRouter, Link } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Button, FormControl, Alert } from 'react-bootstrap';
import { toJS, fromJS } from 'immutable';
import AddButton from './AddButton';
import ExpandableSubsection from './ExpandableSubsection';
import Simulate from './Simulate';
import Publish from './Publish';
import ClassifiersList from './ClassifiersList';
import LearnersList from './LearnersList';
import HistoryButtons from './HistoryButtons';
import InfoIcon from 'base/components/InfoIcon';
import EditableText from 'base/components/EditableText';
import Collaborators from 'base/components/Collaborators';

import 'create-experiment/scss/app.scss';

import { EXPERIMENT } from 'base/redux/modules/collaborators_module';
import { getFromServer, addClassifier, defaultClassifier, saveCurrentExperimentOnServer, resetEditError, trainOnServer } from 'create-experiment/redux/modules/create_experiment_module';
import { reset as resetSimulation } from 'create-experiment/redux/modules/simulate_module';

class ContentComponent extends React.Component {
  constructor(props) {
    super(props)
    this._addClassifier = this._addClassifier.bind(this);
    this._getRetrainUuids = this._getRetrainUuids.bind(this);
    this._handleEditName = this._handleEditName.bind(this);
    this._handleCancelEditName = this._handleCancelEditName.bind(this);
    this._handleRetrainClick = this._handleRetrainClick.bind(this);
    this.state = {
      name: this.props.name
    }
  }

  componentDidMount() {
    const { params, getFromServer, resetSimulation } = this.props;
    getFromServer(params.id);
    resetSimulation();
  }

  _addClassifier(type) {
    const { addClassifier, saveCurrentExperimentOnServer } = this.props;
    addClassifier( defaultClassifier(type) );
    saveCurrentExperimentOnServer()
  }

  _getRetrainUuids(formula) {
    return formula.filter(item => {
      const clf = item.get('classifier');
      const isTrainedType = clf.get('type') === 'trained';
      const isDatasets = clf.get('datasets') && clf.get('datasets').size > 0;
      const isDirty = clf.get('dirty') === true;
      const isTraining = clf.get('training') === true;
      return isTrainedType && isDatasets && isDirty && !isTraining;
    }).map(item => item.get('uuid'));
  }

  _handleEditName(name) {
    const { saveCurrentExperimentOnServer } = this.props;
    return saveCurrentExperimentOnServer({ name });
  }

  _handleCancelEditName() {
    this.props.resetEditError()
  }

  _handleRetrainClick(retrainUuids) {
    this.props.trainOnServer(retrainUuids)
  }

  render() {
    const { id, formula, errorMessage, name, isOwner, ownerUsername, params, saveCurrentExperimentOnServer } = this.props;
    const canNotBeProcessed = !formula.size;
    const infoMessagesMap = {
      'No classifiers. Use the +Add button': !formula.size
    }
    const retrainUuids = this._getRetrainUuids(formula);

    return (
      <Grid fluid={true}>
        <div className="experiment">
          <div className="experiment-top clearfix">
            { +params.id === id && ( // after we've successfully got experiment with needed id
              <Collaborators
                isOwner={isOwner}
                ownerUsername={ownerUsername}
                entity={EXPERIMENT}
                id={id} />
            ) }

            <EditableText
              className="experiment-name"
              text={ name }
              onSave={ this._handleEditName }
              onCancel={ this._handleCancelEditName }
              asyncSave
            />
          </div>

          { !!errorMessage && <Alert bsStyle="danger">{ errorMessage }</Alert> }

          <hr />

          <HistoryButtons />

          <div className="experiment-list">
            <LearnersList />

            <ClassifiersList />
          </div>

          <div className="classifiers-bottom clearfix">
            <AddButton onClick={this._addClassifier} />
            <button
              disabled={retrainUuids.size === 0}
              className="classifiers-retrain"
              onClick={() => this._handleRetrainClick(retrainUuids)}>
              <i className="fa fa-redo" />
              Retrain all
            </button>
          </div>

          <hr />

          <ExpandableSubsection
            title="Simulate">
            <Simulate errorMessage={canNotBeProcessed ? 'No classifiers. Use the +Add button' : ''} />
          </ExpandableSubsection>

          <ExpandableSubsection
            title="Publish" iconClass="fa fa-space-shuttle">
            <Publish errorMessage={canNotBeProcessed ? 'No classifiers. Use the +Add button' : ''} />
          </ExpandableSubsection>

          <hr />

          <div className="history-buttons">
            <Link
              disabled={canNotBeProcessed}
              to={`/experiments/${params.id}/evaluate`}
              className="btn btn-primary">
              <i className="fa fa-fw fa-chart-area"/> Evaluate
            </Link>

            { canNotBeProcessed && <InfoIcon messagesMap={infoMessagesMap} /> }
          </div>
        </div>
      </Grid>
    );
  }
}

ContentComponent.propTypes = {
};

const mapStateToProps = (state) => {
  return {
    formula: state.createExperimentModule.get('formula'),
    name: state.createExperimentModule.get('name'),
    id: state.createExperimentModule.get('id'),
    isOwner: state.createExperimentModule.get('isOwner'),
    ownerUsername: state.createExperimentModule.get('ownerUsername'),
    errorMessage: state.createExperimentModule.get('editErrorMessage')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    addClassifier,
    saveCurrentExperimentOnServer,
    resetEditError,
    trainOnServer,
    resetSimulation
  }, dispatch)
}

export default withRouter( connect(mapStateToProps, mapDispatchToProps)(ContentComponent) );
