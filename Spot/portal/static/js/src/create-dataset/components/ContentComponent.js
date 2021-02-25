import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Link } from 'react-router';
import { Grid, FormControl, Table, Alert, Button } from 'react-bootstrap';
import Confirm from 'react-confirm-bootstrap';
import Papa from 'papaparse';
import DataTable from './DataTable';
import MappingInfoModal from './MappingInfoModal';
import InfoIcon from 'base/components/InfoIcon';
import CustomSlider from 'base/components/Slider';
import AllUnmarked from 'base/components/AllUnmarked';
import LabelItem from 'base/components/LabelItem';

import 'create-dataset/scss/app.scss';

import {
  loadDataset,
  clearDataset,
  postToServer,
  setLabelStatus,
  resetLabelStatus,
  setUnmarkedLabelsStatuses
} from 'create-dataset/redux/modules/create_dataset_module';

class ContentComponent extends React.Component {
  constructor(props) {
    super(props)
    this._loadFile = this._loadFile.bind(this);
    this._handleInputChange = this._handleInputChange.bind(this);
    this._saveDataset = this._saveDataset.bind(this);
    this._prepareDataToSave = this._prepareDataToSave.bind(this);
    this.handleSliderChange = this.handleSliderChange.bind(this);
    this._addDescription = this._addDescription.bind(this);
    this._getLabelStatus = this._getLabelStatus.bind(this);
    this._renderLabels = this._renderLabels.bind(this);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);

    this.state = {
      filename: '',
      errorMessage: '',
      sliderPercentage: 80,
      testingRows: 0,
      trainingRows: 0,
      isDescription: false,
      showModal: false
    }
  }

  componentDidMount() {
    this.props.clearDataset();
  }

  componentWillReceiveProps(nextProps) {
    if(nextProps.datasetSaved) {
      this.setState({ filename: '', errorMessage: '' })
    }
    const { data } = nextProps;
    const trainingRows = Math.ceil(data.size*80/100);
    const testingRows = data.size - Math.ceil(data.size*80/100);

    this.setState({
      testingRows: testingRows,
      trainingRows: trainingRows
    })
  }

  _isAllowedExtention(filename) {
    const ext = filename.split('.').pop();
    return ext.toLowerCase() === 'csv';
  }

  _loadFile(e) {
    const reader = new FileReader();
    const file = e.target.files[0];
    const { loadDataset, clearDataset } = this.props;

    if(file) {
      clearDataset();
      e.target.value = ''; // reset <input type="file"> so that onChange event works properly

      reader.onload = function() {
        const parsed = Papa.parse(this.result, { skipEmptyLines: true }).data;
        loadDataset(parsed);
      }

      if( this._isAllowedExtention(file.name) ) {
        this.setState({
          filename: file.name,
          errorMessage: '',
          isDescription: false
        });
        reader.readAsText(file);
      } else {
        this.setState({
          filename: '',
          errorMessage: 'Wrong file format. Please use .csv',
          isDescription: false
        })
      }
    }
  }

  _handleInputChange(e) {
    this.setState({ [e.target.name]: e.target.value });
  }

  _isValidFilename(filename) {
    return filename !== '';
  }

  _prepareDataToSave(data) {
    const { labelIndex, bodyIndex, isHeaderRemoved } = this.props;
    const { sliderPercentage, trainingRows, testingRows } = this.state;
    const d = isHeaderRemoved ? data.remove(0) : data;

    let filtered = d.toJS().reduce((obj, row) => {
      obj.body.push(row[bodyIndex]);
      obj.labels.push(row[labelIndex]);
      return obj;
    }, { body: [], labels: [] });

    filtered.trainingPercentage = sliderPercentage;
    filtered.trainingRows = trainingRows;
    filtered.testingRows = testingRows;

    return filtered;
  }

  _saveDataset() {
    const { postToServer, data, pos, neg, isHeaderRemoved } = this.props;
    const { filename, description } = this.state;
    const preparedData = this._prepareDataToSave(data);
    const mapping = pos.size > 0 && neg.size > 0 ? { pos: pos.toJS(), neg: neg.toJS() } : null;

    if( this._isValidFilename(filename) ) {
      postToServer(filename, description, preparedData, mapping);
    }
  }

  _addDescription() {
    this.setState({ isDescription: !this.state.isDescription })
  }

  handleSliderChange(value){
    const { data } = this.props;
    const trainingRows = Math.ceil(data.size*value/100);
    const testingRows = data.size - Math.ceil(data.size*value/100);

    this.setState({
      sliderPercentage: value,
      trainingRows: trainingRows,
      testingRows: testingRows
    })
  }

  _getLabelStatus(label, pos, neg) {
    if(pos.indexOf(label) !== -1) {
      return 'pos';
    } else if(neg.indexOf(label) !== -1) {
      return 'neg';
    } else {
      return 'def';
    }
  }

  _renderLabels(labels) {
    const { pos, neg, setLabelStatus, resetLabelStatus } = this.props;
    return labels.map((label, i) => (
      <LabelItem
        key={i}
        title={label}
        status={this._getLabelStatus(label, pos, neg)}
        onSetStatus={setLabelStatus}
        onResetStatus={resetLabelStatus}
      />
    ))
  }

  _showModal() {
    this.setState({ showModal: true });
  }

  _hideModal() {
    this.setState({ showModal: false });
  }

  render() {
    const { filename, description, errorMessage, isDescription, showModal } = this.state;
    const { data, labels, pos, neg, setUnmarkedLabelsStatuses, datasetSaving, datasetSaved, savedDatasetData, bodyIndex, labelIndex } = this.props;
    const supervised = bodyIndex !== null && labelIndex !== null;
    const isLessThanTwoLabels = pos.size === 0 || neg.size === 0;
    const canNotBeSaved = !filename || bodyIndex === null || (supervised && isLessThanTwoLabels);
    const infoMessagesMap = {
      "Filename is not valid": !filename,
      "Need to define the useful columns": bodyIndex === null,
      "Choose at least one positive and one negative label": supervised && isLessThanTwoLabels
    }
    const confirmModalContent = (
      <div className="confirm">
        <div className="confirm-block">"Ok" to save this as Unsupervised Dataset</div>
        <div>"Cancel" and select a <code>Labels</code> column to turn it into Supervised Dataset</div>
      </div>
    )

    if(datasetSaving) return <div className="spinner spinner--center" />;

    return (
      <div>
        <Grid fluid={true}>
          <h1>Create new dataset</h1>
          <hr />

          {/* load file */}
          <div className="file">
            <label
              className="file-button"
              htmlFor="file-input">
              <i className="fa fa-upload" />
              Load CSV
            </label>

            <FormControl
              className="file-input"
              id="file-input"
              type="file"
              accept=".csv"
              onChange={this._loadFile} />
          </div>

          <hr />

          { data.size > 0 && (
            <div className="create-dataset-form">
              <div className="form-group">
                <label className="wrap-label">Name: </label>
                <div className="wrap-input">
                  <FormControl
                    type="text"
                    value={filename}
                    name="filename"
                    onChange={this._handleInputChange} />
                </div>
              </div>

              { isDescription ? (
                <div className="form-group">
                  <label className="wrap-label">Description: </label>
                  <div className="wrap-input">
                    <FormControl
                      componentClass="textarea"
                      value={description}
                      name="description"
                      maxLength="500"
                      placeholder="Optional"
                      onChange={this._handleInputChange} />
                  </div>
                </div>
              ) : (
                <span
                  className="create-dataset-add-field"
                  onClick={this._addDescription}>
                  <i className="fa fa-plus" />
                  Add description
                </span>
              ) }
            </div>
          ) }

          { !!errorMessage && (
            <Alert
              bsStyle="danger"
              className="file-error">{ errorMessage }</Alert>
          ) }

          { datasetSaved && (
            <Alert
              bsStyle="success"
              className="file-success-saved">
              Dataset saved successfully
              <Link
                className="saved-dataset-link"
                to={`/datasets/${savedDatasetData.get('id')}/page/1`}>
                <i className="fa fa-database" />
                <span>{ savedDatasetData.get('name') }</span>
              </Link>
            </Alert>
          ) }

          { data.size > 0 && (
            <div>
              <DataTable data={data} />

              <hr />

              { supervised && labels.size > 0 && (
                <div className="create-dataset-mapping">
                  <strong className="create-dataset-mapping-title">
                    Labels mapping
                    <i
                      className="fa fa-question-square"
                      onClick={this._showModal} />
                  </strong>

                  <MappingInfoModal
                    show={showModal}
                    onHide={this._hideModal} />

                  <AllUnmarked
                    onPosClick={() => { setUnmarkedLabelsStatuses('pos') }}
                    onNegClick={() => { setUnmarkedLabelsStatuses('neg') }} />

                  <div className="label-items-list">
                    { this._renderLabels(labels) }
                  </div>

                  <hr />
                </div>
              ) }

              <div className="create-dataset-bottom-tools">
                { supervised ? (
                  <Button
                    bsStyle="success"
                    disabled={canNotBeSaved}
                    onClick={this._saveDataset}>Save</Button>
                ) : (
                  <Confirm
                    onConfirm={this._saveDataset}
                    title="Saving as Unsupervised?"
                    confirmText="Ok"
                    confirmBSStyle="success"
                    body={confirmModalContent}>
                    <Button
                      bsStyle="success"
                      disabled={canNotBeSaved}>Save</Button>
                  </Confirm>
                )}

                { canNotBeSaved && <InfoIcon messagesMap={infoMessagesMap} /> }

                { supervised && (
                  <div className="create-dataset-slider">
                    <CustomSlider
                      sliderPercentage={this.state.sliderPercentage}
                      labelLeft={<span>Training<br />{this.state.trainingRows} rows</span>}
                      labelRight={<span>Testing<br />{this.state.testingRows} rows</span>}
                      handleSliderChange={this.handleSliderChange}
                      infoMessage="Specify the split ratio (how much of the data will be training and how much testing)"
                    />
                  </div>
                ) }
              </div>
            </div>

          )}
        </Grid>
      </div>
    );
  }
}

ContentComponent.defaultProps = {
};

const mapStateToProps = (state) => {
  return {
    datasetSaving: state.createDatasetModule.get('datasetSaving'),
    datasetSaved: state.createDatasetModule.get('datasetSaved'),
    savedDatasetData: state.createDatasetModule.get('savedDatasetData'),
    data: state.createDatasetModule.get('dataset'),
    labels: state.createDatasetModule.get('labels'),
    pos: state.createDatasetModule.get('pos'),
    neg: state.createDatasetModule.get('neg'),
    bodyIndex: state.createDatasetModule.get('bodyIndex'),
    labelIndex: state.createDatasetModule.get('labelIndex'),
    isHeaderRemoved: state.createDatasetModule.get('isHeaderRemoved')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    loadDataset,
    clearDataset,
    postToServer,
    setLabelStatus,
    resetLabelStatus,
    setUnmarkedLabelsStatuses
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
