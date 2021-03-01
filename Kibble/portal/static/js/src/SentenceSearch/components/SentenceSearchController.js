import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import axios from 'axios';
import {
  ListGroup,
  ListGroupItem,
  Grid,
  Col,
  Row,
  Panel,
  Button,
  Glyphicon,
  ButtonToolbar
} from 'react-bootstrap';

import { getBatchForProject } from 'base/redux/modules/batches';
import { getReportForBatch, SENTENCE_TYPE } from 'base/redux/modules/reports';
import { getProjects } from 'base/redux/modules/projects';
import { getSentences } from 'base/redux/modules/sentencepulling';
import {
    setSelectedBatchId,
    setSelectedProjectId,
    setSelectedReport,
    setModalOpen,
    bulkDownloadTaskSetState,
    clearBulkDownloadUrl,
    changeSentenceInput
} from 'SentenceSearch/redux/actions';
import ProjectSelect from 'base/components/ProjectSelect';
import { MODULE_NAME } from 'SentenceSearch/constants';
import { all } from 'base/utils/misc';
import { Spinner } from 'base/components/misc'


const formSelectStyle = {
  background: '#f7f7f7',
  padding: '15px 0',
  marginBottom: 30,
  borderRadius: 5
};

const BatchListItem = ({ active, batch, handleSelect }) =>
  <ListGroupItem
    active={active}
    disabled={batch.sentences_count === 0}
    title={batch.sentences_count === 0 ? 'batch have no sentences' : ''}
    onClick={() => handleSelect(batch)}
  >
    {batch.name}
  </ListGroupItem>;


const BatchAndReportBlock = ({ batches, selectedBatchId, selectedReport, onBatchSelect, onReportSelect, reports, display, loadingReports }) => {
  if (!display) return null;

  return (
    <Row>
      <Col xs={6} md={6}>
        <h4>Batches</h4>
        <div className="project-list-selector">
          <ListGroup>
            {batches.map(batch =>
              <BatchListItem
                key={batch.id}
                batch={batch}
                active={batch.id === selectedBatchId}
                handleSelect={onBatchSelect}
              />)}
          </ListGroup>
        </div>
      </Col>
      <Col xs={6} md={6}>
        <h4>Reports</h4>
        <div className="project-list-selector">
        { loadingReports ? <Spinner style={{margin: 'auto'}} /> : reports.map((report) =>
            <ListGroupItem
              key={report.uuid}
              active={report.uuid === selectedReport.get('uuid')}
              onClick={() => onReportSelect(report)}
            >
              {report.name}
            </ListGroupItem>
          )}
        </div>
      </Col>
    </Row>
  )
};


class SentencesSearchController extends React.Component {
  constructor(props) {
    super(props);

    this.selectProject = this.selectProject.bind(this);
    this.selectBatch = this.selectBatch.bind(this);
    this.selectReport = this.selectReport.bind(this);
    this.searchForSentences = this.searchForSentences.bind(this);
    this.showPreview = this.showPreview.bind(this);
    this.handleBulkDownloadJSON = this.handleBulkDownloadJSON.bind(this);
    this.handleBulkDownloadCSV = this.handleBulkDownloadCSV.bind(this);
    this.handleSingleDownloadCSV = this.handleSingleDownloadCSV.bind(this);
    this.handleSingleDownloadJSON = this.handleSingleDownloadJSON.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.bulkDownloadUrl) {
      window.open(nextProps.bulkDownloadUrl, '_blank');
      this.props.clearBulkDownloadUrl();
    }
  }

  selectProject(projectId) {
    this.props.setSelectedProjectId(projectId);
    if (projectId) {
      this.props.getBatchForProject(projectId, MODULE_NAME);
    }
  }

  selectBatch(batch) {
    // ignore empty batch clicks
    if (batch && !batch.sentences_count) return;
    if (batch) {
      this.props.getReportForBatch(batch.id, SENTENCE_TYPE, MODULE_NAME);
      this.props.setSelectedBatchId(batch.id);
    }
  }

  selectReport(report) {
    if (report) {
      this.props.setSelectedReport(report.uuid);
    }
  }

  searchForSentences() {
    const { inputSentence, selectedBatchId, getSentences, changeSentenceInput } = this.props;
    if(inputSentence && selectedBatchId) {
      const data = {
        sentence: inputSentence,
        batch: selectedBatchId
      }
      getSentences(data);
      changeSentenceInput('');
    }
  }


  showPreview() {
    this.props.setModalOpen('preview', true);
  }

  handleBulkDownloadJSON() {
    this.props.bulkDownloadTaskSetState(true);
    axios.get(`${window.CONFIG.API_URLS.downloadReport}?batch=${this.props.selectedBatchId}&report_type=${SENTENCE_TYPE}&json=1`)
      .catch(() => this.props.bulkDownloadTaskSetState(false))
  }

  handleBulkDownloadCSV() {
    this.props.bulkDownloadTaskSetState(true);
    axios.get(`${window.CONFIG.API_URLS.downloadReport}?batch=${this.props.selectedBatchId}&report_type=${SENTENCE_TYPE}`)
      .catch(() => this.props.bulkDownloadTaskSetState(false))
  }

  handleSingleDownloadCSV() {
      window.open(`${window.CONFIG.API_URLS.downloadReport}?report=${this.props.selectedReport.get('id')}`, '_blank');
  }

  handleSingleDownloadJSON() {
      window.open(`${window.CONFIG.API_URLS.downloadReport}?report=${this.props.selectedReport.get('id')}&json=1`, '_blank');
  }

  handleInputChange(e) {
    this.props.changeSentenceInput(e.target.value);
  }

  render() {
    const {
      selectedKeywordList,
      selectedBatchId,
      selectedProjectId,
      selectedReport,
      batches,
      reports,
      loadingReports,
      bulkDownloadTaskState,
      inputSentence
    } = this.props;
    const applyButton = all(selectedBatchId, inputSentence.length);
    const previewButton = all(selectedBatchId, selectedReport.size);
    const bulkDownload = !(bulkDownloadTaskState || Boolean(selectedBatchId));

    return (
      <Grid>
        <Col xs={12} md={12} sm={12}>
        <Row className="formSelectStyle">
          <div className="row-title">Search Similar Sentences</div>
            <Row className="no-margin-row">
              <Col xs={12} md={12} sm={12}>
                <h4>Generate similar sentences with:</h4>
                <div className="input-wrapper">
                  <textarea
                    value={inputSentence}
                    name="inputSentence"
                    className="add-keyword-input"
                    placeholder="Type a sentence..."
                    onChange={this.handleInputChange}
                    onKeyDown={e => e.keyCode === 13 && this.searchForSentences()}/>
                </div>
              </Col>
            </Row>
            <Row className="no-margin-row">
              <Col xs={12} md={12} sm={12}>
                <ProjectSelect
                  preSelected={selectedProjectId}
                  onChange={this.selectProject}
                  displayAllOption={false}
                />
                <BatchAndReportBlock
                  display={selectedProjectId > 0}
                  batches={batches}
                  reports={reports}
                  selectedBatchId={selectedBatchId}
                  selectedReport={selectedReport}
                  onBatchSelect={this.selectBatch}
                  onReportSelect={this.selectReport}
                  loadingReports={loadingReports}
                />
              </Col>
            </Row>
            <Row className="no-margin-row">
              <div className="submit-list-wrapper">
                <ButtonToolbar>
                  <Button onClick={this.searchForSentences} disabled={!applyButton}>
                    { !applyButton ? 'Input a sentence and select batch' : 'Process' }
                  </Button>
                  <Button onClick={this.showPreview} disabled={!previewButton}>
                    { !previewButton ? 'Select batch and report first' : 'Preview' }
                  </Button>
                </ButtonToolbar>
                <ButtonToolbar>
                  <Button onClick={this.handleSingleDownloadJSON}
                          disabled={!Boolean(selectedReport.size)}>
                    <Glyphicon glyph='download-alt'/>
                    { ' JSON Report' }
                  </Button>
                  <Button onClick={this.handleSingleDownloadCSV}
                          disabled={!Boolean(selectedReport.size)}>
                    <Glyphicon glyph='download-alt'/>
                    { ' CSV Report' }
                  </Button>
                  <Button onClick={this.handleBulkDownloadCSV}
                          disabled={bulkDownload}>
                    <Glyphicon glyph='download-alt'/>
                    {
                      bulkDownloadTaskState ? ' Please wait' : ' All CSV'
                    }
                  </Button>
                  <Button onClick={this.handleBulkDownloadJSON}
                          disabled={bulkDownload}>
                    <Glyphicon glyph='download-alt'/>
                    {
                      bulkDownloadTaskState ? ' Please wait' : ' All JSON'
                    }
                  </Button>
                  </ButtonToolbar>
                </div>
            </Row>
          </Row>
        </Col>
      </Grid>
    );
  }
}

export default connect(
  (state) => ({
    batches: state[ MODULE_NAME ].get('project_batches'),
    reports: state[ MODULE_NAME ].get('reports'),
    inputSentence: state[ MODULE_NAME ].get('inputSentence'),
    selectedBatchId: state[ MODULE_NAME ].get('selectedBatchId'),
    selectedProjectId: state[ MODULE_NAME ].get('selectedProjectId'),
    selectedReport: state[ MODULE_NAME ].get('selectedReport'),
    loadingReports: state[ MODULE_NAME ].get('loadingReports'),
    bulkDownloadTaskState: state[ MODULE_NAME ].get('bulkDownloadTaskState'),
    bulkDownloadUrl: state[ MODULE_NAME ].get('bulkDownloadUrl')
  }),
  (dispatch) => bindActionCreators({
    getBatchForProject,
    changeSentenceInput,
    getReportForBatch,
    setSelectedBatchId,
    setSelectedProjectId,
    setSelectedReport,
    setModalOpen,
    bulkDownloadTaskSetState,
    clearBulkDownloadUrl,
    getSentences
  }, dispatch)
)(SentencesSearchController);
