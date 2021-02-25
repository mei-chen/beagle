import React, { PropTypes } from 'react';
import { withRouter } from 'react-router';
import { Modal, ModalHeader, ModalBody, ButtonGroup, Button, Alert } from 'react-bootstrap';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List, toJS, fromJS } from 'immutable';
import uuidV4 from 'uuid/v4'
import PreviewTable from 'base/components/PreviewTable';
import DiffTable from './DiffTable';
import Scores from './Scores';
import AsyncActionButton from './AsyncActionButton';
import DroppableSection from './DroppableSection';
import Count from './Count';
import Truncate from 'base/components/Truncate';
import AddDatasetModal from 'base/components/AddDatasetModal';
import MappingPreview from 'base/components/MappingPreview';
import { getFromServer as getDatasetsFromServer } from 'datasets/redux/modules/datasets_module';
import { addDataset, getPreviewFromServer, clearEvaluation, getCachedData, setCachedData, setSplitStatus } from 'evaluate/redux/modules/preview_module';
import { evaluateOnServer } from 'evaluate/redux/modules/evaluate_module';
import { generateOnServer } from 'evaluate/redux/modules/generate_module';

import 'evaluate/scss/app.scss';
class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this._showDatasetModal = this._showDatasetModal.bind(this);
    this._hideDatasetModal = this._hideDatasetModal.bind(this);
    this._showDiffModal = this._showDiffModal.bind(this);
    this._hideDiffModal = this._hideDiffModal.bind(this);
    this._addDataset = this._addDataset.bind(this);
    this._evaluate = this._evaluate.bind(this);
    this._generatePredicted = this._generatePredicted.bind(this);
    this._setSplit = this._setSplit.bind(this);
    this._mappingToSend = this._mappingToSend.bind(this);
    this.state = {
      showDatasetModal: false,
      showDiffModal: false
    }
  }

  componentDidMount() {
    const { clearEvaluation, getDatasetsFromServer, getCachedData } = this.props;
    const { id:experimentId } = this.props.params;

    clearEvaluation();
    getDatasetsFromServer();
    getCachedData(experimentId)
      .then( res => this._addDataset(fromJS(res.data), false) )
      .catch(err => console.log('No cached dataset'))
  }

  _hideDatasetModal() {
    this.setState({ showDatasetModal: false })
  }

  _showDatasetModal() {
    this.setState({ showDatasetModal: true })
  }

  _hideDiffModal() {
    this.setState({ showDiffModal: false })
  }

  _showDiffModal() {
    this.setState({ showDiffModal: true })
  }

  _mappingToSend(mapping) {
    const unsupervised = !mapping || mapping.size === 0;
    return !unsupervised ? mapping.toJS() : null;
  }

  _addDataset(chosenDataset, saveCache=true) {
    const { addDataset, getPreviewFromServer, clearEvaluation, setCachedData } = this.props;
    const { id:experimentId } = this.props.params;
    const defaultSplit = true;

    const id = chosenDataset.get('id');
    const mapping = chosenDataset.get('mapping') || null;
    this.setState({ showDatasetModal: false });

    clearEvaluation()
    addDataset( chosenDataset.toJS() );
    getPreviewFromServer(id, mapping, defaultSplit);
    saveCache && setCachedData( experimentId, chosenDataset.toJS() )
  }

  _evaluate() {
    const { dataset, mapping, isSplit, evaluateOnServer } = this.props;
    const { id:experimentId } = this.props.params;
    const datasetId = dataset.get('id');

    evaluateOnServer(uuidV4(), experimentId, {
      id: datasetId,
      mapping: this._mappingToSend(mapping),
      split: isSplit
    })
  }

  _generatePredicted() {
    const { dataset, mapping, isSplit, generateOnServer } = this.props;
    const { id:experimentId } = this.props.params;
    const datasetId = dataset.get('id');

    generateOnServer(uuidV4(), experimentId, {
      id: datasetId,
      mapping: this._mappingToSend(mapping),
      split: isSplit
    })
  }

  _setSplit(split) {
    const { dataset, mapping, setSplitStatus, getPreviewFromServer } = this.props;
    const id = dataset.get('id');

    setSplitStatus(split);
    getPreviewFromServer(id, this._mappingToSend(mapping), split);
  }

  render() {
    const { showDatasetModal, showDiffModal } = this.state;
    const { id:experimentId } = this.props.params;
    const { datasets, dataset, mapping, isSplit, scores,
            isEvaluating, isGenerating,
            previewError, generationError, evaluationError,
            previewSamples, previewStats,
            generatedSamples, generatedStats } = this.props;
    const unsupervised = !mapping || mapping.size === 0;

    return (
      <div>
        {/* DATASET INFO */}
        <div className="evaluate-dataset-top">
          { dataset.size > 0 && (
            <span className="evaluate-dataset-info">
              <i className="evaluate-dataset-icon fa fa-database" />

              <div className="evaluate-dataset-name">
                <Truncate maxLength={35}>{ dataset.get('name') }</Truncate>
                { !unsupervised && <MappingPreview mapping={ mapping } /> }
              </div>

              <ButtonGroup className="evaluate-dataset-split">
                <Button
                  active={!isSplit}
                  onClick={() => { this._setSplit(false) }} >
                  Full dataset
                </Button>
                <Button
                  active={isSplit}
                  onClick={() => { this._setSplit(true) }} >
                  Test split
                </Button>
              </ButtonGroup>
            </span>
          ) }

          <Button
            onClick={this._showDatasetModal}>
            Choose dataset
          </Button>
        </div>

        { !!previewError && <Alert className="evaluate-dataset-error" bsStyle="danger">{ previewError }</Alert> }

        {/* PREVIEW */}
        { previewSamples.size > 0 && (
          <DroppableSection title="Preview">
            <PreviewTable data={previewSamples} />
            <Count {...previewStats.toJS()} />
          </DroppableSection>
        ) }

        {/* PREDICTIONS */}
        { generatedSamples.size > 0 && (
          <DroppableSection title="Predicted">
            {/* export and diff buttons */}
            <div className="dataset-preview-icons">
              { !unsupervised && (
                <button className="action-button" onClick={this._showDiffModal}>
                  <i className="fa fa-tasks" /> <span>Show Diff</span>
                </button>
              ) }
              <a href={`/api/v1/export_predicted/${experimentId}`} className="action-button">
                <i className="fa fa-download" /> <span>Export CSV</span>
              </a>
            </div>

            {/* table */}
            <PreviewTable data={generatedSamples} />
            <Count {...generatedStats.toJS()} />

            {/* diff modal */}
            <Modal show={showDiffModal} onHide={this._hideDiffModal} className="diff-modal">
              <ModalHeader closeButton />
              <ModalBody>
                <DiffTable id={+experimentId} />
              </ModalBody>
            </Modal>
          </DroppableSection>
        ) }

        {/* SCORES */}
        { scores.size > 0 && <Scores /> }

        {/* ERRORS */}
        { !!evaluationError && <Alert bsStyle="danger">{ evaluationError }</Alert> }

        { !!generationError && <Alert bsStyle="danger">{ generationError }</Alert> }

        {/* ACTION BUTTONS */}
        { dataset.size > 0 && (
          <div className="evaluate-dataset-buttons">
            { !unsupervised && (
              <AsyncActionButton
                onClick={this._evaluate}
                isWaiting={ isEvaluating }
                waitingText="Evaluating...">
                Evaluate
              </AsyncActionButton>
            ) }

            <AsyncActionButton
              onClick={this._generatePredicted}
              isWaiting={ isGenerating }
              waitingText="Generating...">
              Generate predicted
            </AsyncActionButton>
          </div>
        ) }

        <AddDatasetModal
          datasets={datasets}
          show={showDatasetModal}
          onHide={this._hideDatasetModal}
          onAddDataset={this._addDataset}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  const pr = state.previewModule,
        ev = state.evaluateModule,
        ge = state.generateModule;

  return {
    datasets: state.datasetsModule.get('datasets'),
    dataset: pr.get('dataset'),
    mapping: pr.get('mapping'),
    isSplit: pr.get('isSplit'),
    previewSamples: pr.get('samples'),
    previewStats: pr.get('stats'),
    generatedSamples: ge.get('samples'),
    generatedStats: ge.get('stats'),
    scores: ev.get('scores'),
    isEvaluating: ev.get('isEvaluating'),
    isGenerating: ge.get('isGenerating'),
    previewError: pr.get('previewError'),
    evaluationError: ev.get('evaluationError'),
    generationError: ge.get('generationError')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getDatasetsFromServer,
    getPreviewFromServer,
    addDataset,
    evaluateOnServer,
    clearEvaluation,
    generateOnServer,
    getCachedData,
    setCachedData,
    setSplitStatus
  }, dispatch)
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(ContentComponent));
