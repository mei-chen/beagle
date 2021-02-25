import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Map, toJS } from 'immutable';
import { OverlayTrigger, Tooltip, FormControl } from 'react-bootstrap';
import Confirm from 'react-confirm-bootstrap';
import RegexDrop from './RegexDrop';
import BuiltInDrop from './BuiltInDrop';
import TrainedDrop from './TrainedDrop';
import enhanceWithClickOutside from 'react-click-outside';
import Weight from './Weight';
import Progress from 'base/components/Progress';

import { editClassifier, removeClassifier, saveCurrentExperimentOnServer, validateRegexOnServer, trainOnServer } from 'create-experiment/redux/modules/create_experiment_module';

class Classifier extends Component {
  constructor(props) {
    super(props);
    this._getClfLabel = this._getClfLabel.bind(this);
    this._getClfIconClass = this._getClfIconClass.bind(this);
    this._getClfButtons = this._getClfButtons.bind(this);
    this._getRetrainButton = this._getRetrainButton.bind(this);
    this._getSaveAndRetrainButton = this._getSaveAndRetrainButton.bind(this);
    this._getClfEditControls = this._getClfEditControls.bind(this);
    this._enableEdit = this._enableEdit.bind(this);
    this._editClassifier = this._editClassifier.bind(this);
    this._cancelEdit = this._cancelEdit.bind(this);
    this._onDropInputChange = this._onDropInputChange.bind(this);
    this._onWeightInputChange = this._onWeightInputChange.bind(this);
    this._deleteClassifier = this._deleteClassifier.bind(this);
    this._handleSaveClick = this._handleSaveClick.bind(this);
    this._handleSaveAndTrainClick = this._handleSaveAndTrainClick.bind(this);
    this._handleRetrainClick = this._handleRetrainClick.bind(this);
    this._onAddDataset = this._onAddDataset.bind(this);
    this._onRemoveDataset = this._onRemoveDataset.bind(this);
    this.state = {
      isEdit: false,
      weight: this.props.weight,
      classifier: this.props.classifier,
      isValidRegex: true,
      isValidatingRegex: false
    }
  }

  handleClickOutside(e) {
    // close drop on outside click except from click on modal window
    if(e.target.closest('.add-dataset-modal') !== null || e.target.closest('.threshold-modal') !== null) return false;
    this.setState({ isEdit: false });
  }

  componentWillReceiveProps(nextProps) {
    // update scores and cofidence to display in dropdown
    if(!this.props.classifier.equals(nextProps.classifier)) {
      this.setState({ classifier: nextProps.classifier });
    }

    // close dropdown on training start
    if(nextProps.classifier.get('training') && !this.props.classifier.get('training')) {
      this.setState({ isEdit: false });
    }
  }

  _enableEdit() {
    this.setState({ isEdit: true })
  }

  _cancelEdit() {
    this.setState({ isEdit: false, classifier: this.props.classifier, isValidRegex: true });
  }

  _editClassifier() {
    const { weight, classifier } = this.state;
    const { index, editClassifier, saveCurrentExperimentOnServer } = this.props;

    editClassifier(index, { weight, classifier });
    return saveCurrentExperimentOnServer();
  }

  _handleSaveClick(type) {
    // classifier of type 'regex' needs validation before saving
    if(type === 'regex') {
      const { validateRegexOnServer } = this.props;
      const regex = this.state.classifier.get('expression');
      this.setState({ isValidatingRegex: true });

      validateRegexOnServer(regex)
        .then((res) => {
          const isValidRegex = res.data.regex_is_valid;
          this.setState({ isValidRegex, isValidatingRegex: false })
          if(isValidRegex) {
            this.setState({ isEdit: false },  () => this._editClassifier())
          }
        });

    } else {
      this._editClassifier();
      this.setState({ isEdit: false })
    }
  }

  _handleSaveAndTrainClick() {
    // edit on server and only then start to train
    const { uuid, trainOnServer } = this.props;
    this._editClassifier().then(res => {
      trainOnServer([uuid]);
    });
  }

  _handleRetrainClick() {
    const { uuid, trainOnServer } = this.props;
    trainOnServer([uuid]);
  }

  _deleteClassifier() {
    const { removeClassifier, index, saveCurrentExperimentOnServer } = this.props;
    removeClassifier(index);
    saveCurrentExperimentOnServer();
  }

  _onWeightInputChange(weight) {
    this.setState({ weight })
  }

  _onDropInputChange(data) {
    this.setState({ classifier: this.state.classifier.merge(data) });
  }

  _onAddDataset(dataset) {
    const classifier = this.state.classifier;
    const datasetId = dataset.get('id');
    this.setState({ classifier: classifier.update('datasets', datasets => datasets.push(dataset)) });
  }

  _onRemoveDataset(index) {
    const classifier = this.state.classifier;
    this.setState({ classifier: classifier.update('datasets', datasets => datasets.remove(index) ) });
  }

  _getClfLabel(classifier) {
    if(classifier.get('type') === 'trained') {
      switch( classifier.get('model') ) {
        case 'logreg': return 'Logistic Regression';
        case 'mlp': return 'Multi-layer Perceptron';
        case 'rf': return 'Random Forest';
        case 'adaboost': return 'AdaBoost SVM';
      }
    } else if(classifier.get('type') === 'regex') {
      return classifier.get('expression')
    }

    return classifier.get('model');
  }

  _getClfIconClass(type) {
    switch(type) {
      case 'regex': {
        return 'fa fa-superscript'
      }
      case 'builtin': {
        return 'fa fa-archive'
      }
      case 'trained': {
        return 'fa fa-magic'
      }
    }
  }

  _getRetrainButton(options) {
    if(options.trainingError) {
      const tooltip = <Tooltip id="tooltip">{ options.trainingError }</Tooltip>
      return (
        <OverlayTrigger placement="top" overlay={tooltip}>
          <i className="fa fa-exclamation-circle text-danger" />
        </OverlayTrigger>
      )
    } else {
      const disabled = options && (!options.hasDatasets || !options.isDirty || options.isTraining);
      return (
        <button
          disabled={disabled}
          className={`clf-button fa fa-redo attention-area ${!disabled ? 'attention-area--in' : ''} ${options.isTraining ? 'fa-spin' : ''}`}
          onClick={this._handleRetrainClick} />
      )
    }
  }

  _getSaveAndRetrainButton(options) {
    const retrainAvailable = options.hasDatasets && options.isDirty && !options.isTraining;
    // if there are NO changes that will make clf dirty AND
    // retrain IS available: display 'Retrain' button
    if(!options.willBeDirty && retrainAvailable) {
      return (
        <button
          disabled={options && (!options.hasDatasets || !options.isDirty || options.isTraining)}
          className="clf-edit-control text-primary"
          onClick={this._handleRetrainClick}>
          <i className="fa fa-fw fa-microchip" />
          Retrain
        </button>
      )
    // otherwise: display 'Save and Retrain' button
    } else {
      return (
        <button
          disabled={!options.willBeDirty}
          className="clf-edit-control text-primary"
          onClick={this._handleSaveAndTrainClick}
          >
          <i className="fa fa-fw fa-microchip" />
          Save and Train
        </button>
      )
    }
  }

  _getClfButtons(type, index, options) {
    const { isEdit } = this.state;

    return (
      <div className="clf-buttons">
        { !isEdit && (
            <span>
              { type === 'trained' && this._getRetrainButton(options) }
              <button
                className="clf-button fa fa-cog"
                disabled={options && options.isTraining}
                onClick={this._enableEdit} />
            </span>
          )
        }

        <Confirm
          onConfirm={this._deleteClassifier}
          title="Delete classifier"
          body="Are you sure?">
          <button className="clf-button fa fa-trash" />
        </Confirm>
      </div>
    )
  }

  _getClfDrop(type) {
    // all changes made in dropdown are stored in this.state (waiting to be saved or canceled)
    // therefore dropdown reflects state.classifier (not props.classifier)
    const { classifier } = this.state;
    const { uuid, confidence } = this.props;

    switch(type) {
      case 'regex': {
        const { isValidRegex } = this.state;
        return (
          <RegexDrop
            regex={classifier.get('expression')}
            apply={classifier.get('apply')}
            onChange={this._onDropInputChange}
            isValidRegex={isValidRegex} />
        )
      }
      case 'builtin': {
        return (
          <BuiltInDrop
            type={classifier.get('model')}
            apply={classifier.get('apply')}
            onChange={this._onDropInputChange} />
        )
      }
      case 'trained': {
        return (
          <TrainedDrop
            uuid={uuid}
            type={classifier.get('model')}
            apply={classifier.get('apply')}
            threshold={classifier.get('decision_threshold')}
            confidence={confidence}
            clfDatasets={classifier.get('datasets')}
            scores={classifier.get('scores')}
            onChange={this._onDropInputChange}
            onAddDataset={this._onAddDataset}
            onRemoveDataset={this._onRemoveDataset} />
        )
      }
    }
  }

  _getClfEditControls(type, options) {
    const { isValidatingRegex } = this.state;

    return (
      <div className="clf-edit-controls">
        { type === 'trained' && this._getSaveAndRetrainButton(options) }
        <button
          disabled={options.isEqual || isValidatingRegex}
          className="clf-edit-control text-success"
          onClick={() => {this._handleSaveClick(type)}}
          >
          <i className="fa fa-check" />
          Save
        </button>
        <button
          disabled={isValidatingRegex}
          className="clf-edit-control"
          onClick={this._cancelEdit}
          >
          <i className="fa fa-times" />
          Cancel
        </button>
      </div>
    )
  }

  render() {
    const { index, classifier, weight, trainingError } = this.props;
    const type = classifier.get('type');
    const name = classifier.get('name');
    const scores = classifier.get('scores');
    const datasets = classifier.get('datasets');
    const apply = classifier.get('apply');
    const model = classifier.get('model');
    const threshold = classifier.get('decision_threshold');
    const editedApply = this.state.classifier.get('apply')
    const editedDatasets = this.state.classifier.get('datasets');
    const editedModel = this.state.classifier.get('model');
    const editedThreshold = this.state.classifier.get('decision_threshold');

    const isEqual = classifier.equals(this.state.classifier) && weight === this.state.weight;
    const willBeDirty = (
      model && model !== editedModel ||
      apply && apply !== editedApply ||
      threshold !== editedThreshold ||
      editedDatasets && editedDatasets.size > 0 && !datasets.equals(editedDatasets)
    );

    const options = {
      isDirty: classifier.get('dirty'),
      isEqual, // compares saved clf (back-end) and changed clf (front-end)
      willBeDirty, // indicates front-end changes in model, apply or datasets
      hasDatasets: datasets && datasets.size > 0,
      isTraining: classifier.get('training'),
      trainingError
    };
    const { isEdit } = this.state;
    const className = isEdit ? 'clf clf--edit' : 'clf';

    return (
      <div className={className}>
        <div className="clf-right">
          { scores && !isEdit && <div className="clf-prog"><Progress value={ scores.get('f1') } /></div> }
          { isEdit && this._getClfEditControls(type, options) }
          { this._getClfButtons(type, index, options) }
        </div>
        <div className="clf-body">
          <Weight
            weight={ weight }
            isEdit={ isEdit }
            onChange={ this._onWeightInputChange }/>
          <span className="clf-icon">
            <i className={this._getClfIconClass(type)} />
            { editedApply === 'exclude' && <i className="clf-exclude fa fa-minus-circle" /> }
          </span>
          <span className="clf-title">
            { isEdit ? (
              <FormControl
                className="clf-title-input"
                maxLength="30"
                type="text"
                value={this.state.classifier.get('name')}
                onChange={(e) => { this._onDropInputChange({ name: e.target.value }) }}
              />
            ) : (
              <span>{ name }</span>
            ) }
          </span>
          { !isEdit && <span className="clf-label">{ this._getClfLabel(classifier) }</span> }
        </div>
        { isEdit && <div className="clf-drop">{ this._getClfDrop(type) }</div> }
      </div>
    )
  }
}

Classifier.propTypes = {
  index: PropTypes.number.isRequired,
  weight: PropTypes.number.isRequired,
  classifier: PropTypes.instanceOf(Map).isRequired,
  trainingError: PropTypes.string
}

const mapStateToProps = (state, ownProps) => {
  return {}
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    editClassifier,
    removeClassifier,
    validateRegexOnServer,
    saveCurrentExperimentOnServer,
    trainOnServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)( enhanceWithClickOutside(Classifier) );
