import React from "react";
import {
  Grid,
  Col,
  Row,
  ListGroup,
  ListGroupItem,
  ButtonToolbar,
  Button
} from "react-bootstrap";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import { PROJECT_NOT_SELECTED, PROJECT_ALL } from "base/components/ProjectSelect";
import ProjectBatchSelectForm from "base/components/ProjectBatchSelectForm";
import { getBatchForProject } from 'base/redux/modules/batches';
import {
  getReportForBatch,
  REGEX_TYPE,
  KEYWORD_TYPE,
  SENTENCE_TYPE
} from 'base/redux/modules/reports';
import {
  resetReportsLists,
  handleReportUnSelect,
  handleReportSelect,
  setModalOpen,
  markSentence,
  getDocsFromServer
} from 'SentencesObfuscation/redux/actions';
import ObfuscationModal from 'SentencesObfuscation/components/ObfuscationLabelingModal';
import DefaultExportSwitch from 'Settings/components/DefaultExportSwitch';
import { MODULE_NAME } from 'SentencesObfuscation/redux/constants';
import { Spinner } from 'base/components/misc.js'

const ReportListItem = ({ active, report, handleSelect }) =>
  <ListGroupItem
    active={active}
    onClick={() => {
      handleSelect(report.id);
    }}
  >
    {report.name}
  </ListGroupItem>;

const ReportsAndDocumentsBlock = ({
  handleReportSelect,
  handleReportUnSelect,
  selectedReports,
  sentences_reports,
  keywords_reports,
  regex_reports,
  default_export,
  batch,
  docs,
  loadingDownloads,
  initializedSettings,
  showDownloads,
  selcetedSentences
}) => {
  if (batch <= 0) return null;
  return (
    <Grid>
      <Col xs={6} md={6}>
        <h4>Reports</h4>
        <div className="project-list-selector">
        {[sentences_reports, keywords_reports, regex_reports].map((report_list, key) =>
          <ListGroup key={key}>
            {report_list.map(report =>
              <ReportListItem
                key={report.id}
                report={report}
                active={selectedReports.includes(report.id)}
                handleSelect={
                    selectedReports.includes(report.id) ? handleReportUnSelect : handleReportSelect
                }
              />)}
          </ListGroup>
        )}
        </div>
      </Col>
      <Col xs={6} md={6}>
        <h4>Download Documents</h4>
        <div className="project-list-selector">
          {!loadingDownloads && showDownloads && initializedSettings &&
            <span>
              <div className="settings-wrapper out-context">
                <DefaultExportSwitch
                  default_export={default_export}
                />
              </div>
              {docs.map((doc, key) =>
              (<div key={key}>
                <i className="fal fa-file-alt"></i>{' '}<a href={`/api/v1/document/${doc.id}/obfuscate?reports=${JSON.stringify(selcetedSentences)}`}>{doc.name}</a>
              </div>))}
              <div>
                <i className="fal fa-archive"></i>{' '}<a href={`/api/v1/batch/${batch}/obfuscate?reports=${JSON.stringify(selcetedSentences)}`}>Download obfuscated batch as zip</a>
              </div>
            </span>
          }
        </div>
      </Col>
    </Grid>
  )
};


class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      projectId: PROJECT_NOT_SELECTED,
      batchId: 0
    };
    this.onProjectChange = this.onProjectChange.bind(this);
    this.onBatchChange = this.onBatchChange.bind(this);
  }

  onProjectChange(projectId) {
    this.props.getBatchForProject(projectId, '/sentencesObfuscation', projectId === PROJECT_ALL);
    this.setState({ projectId: projectId, batchId: 0 });
    this.props.resetReportsLists();
  };

  onBatchChange(batchId) {
    this.setState({ batchId: batchId });
    batchId > 0 && this.props.getDocsFromServer(batchId);
    this.props.getReportForBatch(batchId, SENTENCE_TYPE, `${SENTENCE_TYPE}/sentencesObfuscation`);
    this.props.getReportForBatch(batchId, KEYWORD_TYPE, `${KEYWORD_TYPE}/sentencesObfuscation`);
    this.props.getReportForBatch(batchId, REGEX_TYPE, `${REGEX_TYPE}/sentencesObfuscation`);
  };

  render() {
    const {
      batches,
      sentences_reports,
      keywords_reports,
      regex_reports,
      selected_reports,
      isModalOpen,
      handleReportUnSelect,
      handleReportSelect,
      setModalOpen,
      markSentence,
      selcetedSentences,
      docs,
      loading_downloads,
      show_downloads,
      default_export,
      initializedSettings
    } = this.props;

    return (
      <div>
        <div className="wrapper">
          <Grid>
            <Col xs={12} md={12} sm={12}>
              <Row className="formSelectStyle">
                <div className="row-title">Sentence Labeling for Obfuscation</div>
                <Row className="no-margin-row">
                  <ProjectBatchSelectForm
                    onProjectChange={this.onProjectChange}
                    onBatchChange={this.onBatchChange}
                    batches={batches}
                  />
                  <ReportsAndDocumentsBlock
                    sentences_reports={sentences_reports}
                    keywords_reports={keywords_reports}
                    regex_reports={regex_reports}
                    handleReportSelect={handleReportSelect}
                    handleReportUnSelect={handleReportUnSelect}
                    batch={this.state.batchId}
                    selectedReports={selected_reports}
                    docs={docs}
                    loadingDownloads={loading_downloads}
                    showDownloads={show_downloads}
                    selcetedSentences={selcetedSentences}
                    default_export={default_export}
                    initializedSettings={initializedSettings}
                  />
                </Row>
                <Row className="no-margin-row">
                  <div className="submit-list-wrapper">
                    <ButtonToolbar>
                      <Button onClick={() => setModalOpen(true)} disabled={!(selected_reports.size > 0)}>
                        { !(selected_reports.size > 0) ? 'Select one or more reports' : 'Start labeling' }
                      </Button>
                    </ButtonToolbar>
                  </div>
                </Row>
              </Row>
            </Col>
          </Grid>
        </div>
        <ObfuscationModal
          isOpen={isModalOpen}
          onClose={() => setModalOpen(false)}
          selected_reports={selected_reports}
          sentences_reports={sentences_reports}
          keywords_reports={keywords_reports}
          regex_reports={regex_reports}
          title="Sentences Labeling for Obfuscation"
        />
      </div>
    );
  }
}

export default connect(
  (state) => ({
    batches: state[ MODULE_NAME ].get('batches'),
    sentences_reports: state[ MODULE_NAME ].get('sentences_reports'),
    keywords_reports: state[ MODULE_NAME ].get('keywords_reports'),
    regex_reports: state[ MODULE_NAME ].get('regex_reports'),
    selected_reports: state[ MODULE_NAME ].get('selected_reports'),
    isModalOpen: state [ MODULE_NAME ].get('isModalOpen'),
    selcetedSentences: state[ MODULE_NAME ].get('selceted_sentences').toJS(),
    docs: state[ MODULE_NAME ].get('docs').toJS(),
    show_downloads: state[ MODULE_NAME ].get('show_downloads'),
    loading_downloads: state[ MODULE_NAME ].get('loading_downloads'),
    default_export: state.settings.get('obfuscated_export_ext'),
    initializedSettings: state.settings.get('isInitialized'),
  }),
  (dispatch) => bindActionCreators({
    getBatchForProject,
    getReportForBatch,
    resetReportsLists,
    handleReportUnSelect,
    handleReportSelect,
    setModalOpen,
    getDocsFromServer
  }, dispatch)
)(ContentComponent);
