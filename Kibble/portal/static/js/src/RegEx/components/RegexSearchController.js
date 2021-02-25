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
import { getReportForBatch, REGEX_TYPE } from 'base/redux/modules/reports';
import { getProjects } from 'base/redux/modules/projects';
import { applyRegEx } from 'base/redux/modules/regexes';
import { batchPropType } from 'BatchManagement/propTypes';
import { projectPropType } from 'ProjectManagement/propTypes';
import { regexPropType, reportPropType } from 'RegEx/propTypes';
import {
    setSelectedBatchId,
    setSelectedRegEx,
    setSelectedProjectId,
    deselectRegEx,
    setSelectedReport,
    setModalOpen,
    bulkDownloadTaskSetState,
    clearBulkDownloadUrl
} from 'RegEx/redux/actions';
import ProjectAndRegexSelect from 'RegEx/components/ProjectRegexSelect';
import { MODULE_NAME } from 'RegEx/constants';
import { all } from 'base/utils/misc';
import { Spinner } from 'base/components/misc';

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
    <Grid>
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
        { loadingReports ? <Spinner style={{margin: '80px auto'}} /> : reports.map((report) =>
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
    </Grid>
  )
};


class RegexSearchController extends React.Component {
  constructor(props) {
    super(props);
    this.selectProject = this.selectProject.bind(this);
    this.selectBatch = this.selectBatch.bind(this);
    this.selectReport = this.selectReport.bind(this);
    this.doApply = this.doApply.bind(this);
    this.selectRegEx = this.selectRegEx.bind(this);
    this.showPreview = this.showPreview.bind(this);
    this.handleBulkDownloadJSON = this.handleBulkDownloadJSON.bind(this);
    this.handleBulkDownloadCSV = this.handleBulkDownloadCSV.bind(this);
    this.handleSingleDownloadCSV = this.handleSingleDownloadCSV.bind(this);
    this.handleSingleDownloadJSON = this.handleSingleDownloadJSON.bind(this);
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
      this.props.getReportForBatch(batch.id, REGEX_TYPE, MODULE_NAME);
      this.props.setSelectedBatchId(batch.id);
    }
  }

  selectReport(report) {
    if (report) {
      this.props.setSelectedReport(report.uuid);
    }
  }

  doApply() {
    this.props.applyRegEx(
      this.props.selectedRegEx.get('id'), this.props.selectedBatchId
    );
  }

  showPreview() {
    this.props.setModalOpen('preview', true);
  }

  selectRegEx(data) {
    if (data) {
      const regex = this.props.regexes.find(el => el.id === data.value);
      this.props.setSelectedRegEx(regex)
    } else {
      this.props.deselectRegEx()
    }
  }

  handleBulkDownloadJSON() {
    this.props.bulkDownloadTaskSetState(true);
    axios.get(`${window.CONFIG.API_URLS.downloadReport}?batch=${this.props.selectedBatchId}&report_type=${REGEX_TYPE}&json=1`)
      .catch(() => this.props.bulkDownloadTaskSetState(false))
  }

  handleBulkDownloadCSV() {
    this.props.bulkDownloadTaskSetState(true);
    axios.get(`${window.CONFIG.API_URLS.downloadReport}?batch=${this.props.selectedBatchId}&report_type=${REGEX_TYPE}`)
      .catch(() => this.props.bulkDownloadTaskSetState(false))
  }

  handleSingleDownloadCSV() {
      window.open(`${window.CONFIG.API_URLS.downloadReport}?report=${this.props.selectedReport.get('id')}`, '_blank');
  }

  handleSingleDownloadJSON() {
      window.open(`${window.CONFIG.API_URLS.downloadReport}?report=${this.props.selectedReport.get('id')}&json=1`, '_blank');
  }

  render() {
    const {
      selectedRegEx,
      selectedBatchId,
      selectedProjectId,
      batches,
      reports,
      loadingReports,
      selectedReport,
      bulkDownloadTaskState,
      setModalOpen,
    } = this.props;
    const applyButton = all(selectedBatchId, selectedRegEx.size);
    const previewButton = all(selectedBatchId, selectedReport.size);
    const bulkDownload = !(bulkDownloadTaskState || Boolean(selectedBatchId));

    return (
      <Grid>
        <Col xs={12} md={12} sm={12}>
          <Row className="formSelectStyle">
            <div className="row-title">RegEx Create and Search</div>
            <Row className="no-margin-row">
              <ProjectAndRegexSelect
                onProjectChange={this.selectProject}
                onRgxChange={this.selectRegEx}
                setModalOpen={setModalOpen}
                selectedRegEx={selectedRegEx}
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
            </Row>
            <Row className="no-margin-row">
              <div className="submit-list-wrapper">
                <ButtonToolbar>
                  <Button onClick={this.doApply} disabled={!applyButton}>
                    { !applyButton ? 'Select regex and batch' : 'Process' }
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
                  <Button onClick={this.handleBulkDownloadCSV} disabled={bulkDownload}>
                    <Glyphicon glyph='download-alt'/>
                    {
                      bulkDownloadTaskState ? ' Please wait' : ' All CSV'
                    }
                  </Button>
                  <Button onClick={this.handleBulkDownloadJSON} disabled={bulkDownload}>
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
    regexes: state[ MODULE_NAME ].get('regexes'),
    reports: state[ MODULE_NAME ].get('reports'),
    selectedRegEx: state[ MODULE_NAME ].get('selectedRegEx'),
    selectedBatchId: state[ MODULE_NAME ].get('selectedBatchId'),
    selectedReport: state[ MODULE_NAME ].get('selectedReport'),
    selectedProjectId: state[ MODULE_NAME ].get('selectedProjectId'),
    loadingReports: state[ MODULE_NAME ].get('loadingReports'),
    bulkDownloadTaskState: state[ MODULE_NAME ].get('bulkDownloadTaskState'),
    bulkDownloadUrl: state[ MODULE_NAME ].get('bulkDownloadUrl')
  }),
  (dispatch) => bindActionCreators({
    getBatchForProject,
    applyRegEx,
    getReportForBatch,
    setSelectedRegEx,
    setSelectedBatchId,
    setSelectedProjectId,
    deselectRegEx,
    setSelectedReport,
    setModalOpen,
    bulkDownloadTaskSetState,
    clearBulkDownloadUrl
  }, dispatch)
)(RegexSearchController);
