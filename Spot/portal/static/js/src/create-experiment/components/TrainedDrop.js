import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List, Map } from 'immutable';
import uuidV4 from 'uuid/v4';
import { Form, FormGroup, DropdownButton, MenuItem, ButtonGroup, Button } from 'react-bootstrap';
import DatasetItem from './DatasetItem';
import AddDatasetModal from 'base/components/AddDatasetModal';
import ThresholdChart from './ThresholdChart';
import ScoresList from 'base/components/ScoresList';

import { getFromServer } from 'datasets/redux/modules/datasets_module';
import { getConfidenceFromServer } from 'create-experiment/redux/modules/create_experiment_module';

const LOGREG = 'logreg';
const MLP = 'mlp';
const RF = 'rf';
const ADABOOST = 'adaboost'

const INCLUDE = 'include';
const EXCLUDE = 'exclude';

class BuiltInDrop extends Component {
  constructor(props) {
    super(props);
    this._getFullType = this._getFullType.bind(this);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._renderDatasetItems = this._renderDatasetItems.bind(this);
    this._addDataset = this._addDataset.bind(this);
    this._getRemainingDatasets = this._getRemainingDatasets.bind(this);
    this._toggleAdvancedDrop = this._toggleAdvancedDrop.bind(this);
    this.state = {
      showModal: false,
      isAdvancedOpen: false,
      isGettingDatasets: false
    }
  }

  componentDidMount() {
    this.setState({ isGettingDatasets: true })
    this.props.getFromServer()
      .then(() => this.setState({ isGettingDatasets: false }))
      .catch(() => () => this.setState({ isGettingDatasets: false }))
  }

  _getFullType(type) {
    if(type === LOGREG) return 'Logistic Regression';
    if(type === MLP) return 'Multi-layer Perceptron';
    if(type === RF) return 'Random Forest';
    if(type === ADABOOST) return 'AdaBoost SVM';
  }

  _showModal() {
    this.setState({ showModal: true });
  }

  _hideModal() {
    this.setState({ showModal: false })
  }

  _renderDatasetItems(clfDatasets) {
    return clfDatasets.map((clfDataset, i) => {

      const isOwner = !!this.props.datasets.find(dataset => dataset.get('id') === clfDataset.get('id'));

      if(!isOwner) {
        return (
          <DatasetItem
            key={uuidV4()}
            inaccessible={true}
            title={clfDataset.get('name')}
            owner={clfDataset.get('owner')}
          />
        )
      };

      return (
        <DatasetItem
          key={uuidV4()}
          index={i}
          title={clfDataset.get('name')}
          onRemove={this.props.onRemoveDataset}
          mapping={clfDataset.get('mapping')}
        />
      )
    })
  }

  _addDataset(dataset) {
    this.props.onAddDataset(dataset);
    this.setState({ showModal: false })
  }

  _getRemainingDatasets(clfDatasets) {
    const clfDatasetsIds = clfDatasets.map(clfDataset => clfDataset.get('id'));
    return this.props.datasets.filter(dataset => clfDatasetsIds.indexOf(dataset.get('id')) === -1);
  }

  _toggleAdvancedDrop() {
    const { uuid, confidence, getConfidenceFromServer } = this.props;
    this.setState({ isAdvancedOpen: !this.state.isAdvancedOpen });
    if(!confidence || !confidence.get('data')) {
      getConfidenceFromServer(uuid)
    }
  }

  render() {
    const { apply, type, threshold, confidence, onChange, onAddDataset, datasets, clfDatasets, scores } = this.props;
    const { showModal, isAdvancedOpen, isGettingDatasets } = this.state;

    return (
      <div className="trained clearfix">
        <span
          className="toggle-link trained-advanced-toggle"
          onClick={this._toggleAdvancedDrop}>
          { isAdvancedOpen ? <i className="fa fa-chevron-double-up" /> : <i className="fa fa-chevron-double-down" /> }
          Advanced
        </span>

        <Form className="trained-form">
          <FormGroup>
            <div className="wrap-label">Type:</div>
            <div className="wrap-input">
              <DropdownButton title={this._getFullType(type)} id={type}>
                <MenuItem
                  onClick={() => onChange({ model: LOGREG }) }>Logistic Regression</MenuItem>
                <MenuItem
                  onClick={() => onChange({ model: MLP }) }>Multi-layer Perceptron</MenuItem>
                <MenuItem
                  onClick={() => onChange({ model: RF }) }>Random Forest</MenuItem>
                <MenuItem
                  onClick={() => onChange({ model: ADABOOST }) }>AdaBoost SVM</MenuItem>
              </DropdownButton>
            </div>
          </FormGroup>
          <FormGroup>
            <div className="wrap-label">Datasets:</div>
            <div className="wrap-input">
              { isGettingDatasets ? (
                <i className="fa fa-spinner fa-pulse fa-fw" />
              ) : (
                <div>
                  <div className="dataset-items-list">
                    { this._renderDatasetItems(clfDatasets) }
                  </div>
                  <Button
                    bsStyle="primary"
                    onClick={this._showModal}>
                    Add
                  </Button>
                </div>
              )}
            </div>
          </FormGroup>
          <FormGroup>
            <div className="wrap-label">Apply</div>
            <div className="wrap-input">
              <ButtonGroup >
                <Button
                  active={apply === INCLUDE}
                  onClick={() => { onChange({ apply: INCLUDE }) }}>
                  Include
                </Button>
                <Button
                  active={apply === EXCLUDE}
                  onClick={() => { onChange({ apply: EXCLUDE }) }}>
                  Exclude
                </Button>
              </ButtonGroup>
            </div>
          </FormGroup>
        </Form>

        <div className="trained-right">
          { !!scores && (
            <div className="trained-scores">
              <ScoresList
                f1={scores.get('f1')}
                precision={scores.get('precision')}
                recall={scores.get('recall')}
              />
            </div>
          ) }

          { isAdvancedOpen && (
            <div className="trained-advanced">
              { !!confidence && (
                <div>
                  <span className="trained-advanced-title">Decision threshold:</span>
                  { confidence.get('isLoading') && <span className="fa fa-spinner fa-spin" /> }
                  { confidence.get('errorMessage') && <span className="text-danger">{ confidence.get('errorMessage') }</span> }
                  { confidence.get('data') && (
                    <ThresholdChart
                      threshold={threshold}
                      range={confidence.get('data').get('range').toJS()}
                      data={confidence.get('data').get('histogram').toJS()}
                      samples={confidence.get('data').get('samples').toJS()}
                      onChange={value => onChange({ decision_threshold: value }) } />
                  ) }
                </div>
              )}
            </div>
          ) }
        </div>

        <AddDatasetModal
          datasets={this._getRemainingDatasets(clfDatasets)}
          show={showModal}
          onHide={this._hideModal}
          onAddDataset={this._addDataset}
          mode="training"
        />
      </div>
    )
  }
}

BuiltInDrop.propTypes = {
  type: PropTypes.oneOf([LOGREG, MLP, RF, ADABOOST]),
  apply: PropTypes.oneOf([INCLUDE, EXCLUDE]),
  threshold: PropTypes.number,
  confidence: PropTypes.instanceOf(Map),
  clfDatasets: PropTypes.instanceOf(List).isRequired,
  datasets: PropTypes.instanceOf(List).isRequired,
  scores: PropTypes.instanceOf(Map),
  onChange: PropTypes.func.isRequired,
  onAddDataset: PropTypes.func.isRequired,
  onRemoveDataset: PropTypes.func.isRequired
}

const mapStateToProps = (state) => {
  return {
    datasets: state.datasetsModule.get('datasets')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    getConfidenceFromServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(BuiltInDrop);
