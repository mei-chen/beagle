import React from "react";
import PropTypes from "prop-types";
import { Modal, Table } from "react-bootstrap";
import { hashHistory } from 'react-router';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import {
    setSelectedBatchId,
    setSelectedProjectId,
    changeSentenceInput
} from 'SentenceSearch/redux/actions';
import { MODULE_NAME as REGEX_MODULE_NAME } from 'RegEx/constants';
import { MODULE_NAME as SENTENCES_MODULE_NAME } from 'SentenceSearch/constants';
import { getBatchForProject } from 'base/redux/modules/batches';
import { getReportForBatch, SENTENCE_TYPE } from 'base/redux/modules/reports';
import { setActiveRootFolder, setActiveUrl } from 'base/redux/modules/sidebar';

class ReportRowComponent extends React.Component {
  constructor(props) {
    super(props);

    this.prepSentencePull = this.prepSentencePull.bind(this);
    this.currentLocationPath = () => hashHistory.getCurrentLocation().pathname;
    this.navTo = this.navTo.bind(this)
  }

  prepSentencePull() {
    const {
      selectedBatchId,
      selectedProjectId,
      changeSentenceInput,
      getReportForBatch,
      setSelectedBatchId,
      setSelectedProjectId,
      setSelectedReport,
      getBatchForProject
    } = this.props;

    setSelectedProjectId(selectedProjectId);
    if (selectedProjectId) {
      getBatchForProject(selectedProjectId, SENTENCES_MODULE_NAME);
    }
    if (selectedBatchId) {
      getReportForBatch(selectedBatchId, SENTENCE_TYPE, SENTENCES_MODULE_NAME);
      setSelectedBatchId(selectedBatchId);
    }
    changeSentenceInput(this.props.report.sentence);
  }

  navTo(page, rootFolder = null) {
    if (this.currentLocationPath() !== page) {
      hashHistory.push(page);
    }
    if (rootFolder) {
      this.props.setActiveRootFolder(rootFolder)
    }
    this.props.setActiveUrl(page);
  }

  render() {
    return (
      <tr key={this.props.reportKey}>
       <td>{this.props.report.batch}</td>
        <td>{this.props.report.regex}</td>
        <td>{this.props.report.found}</td>
        <td>{this.props.report.sentence}</td>
        <td>
          <div className="link-wrapper">
            <a onClick={() => {this.prepSentencePull(); this.navTo('/sentences', 'Sentence')}}>
              <i className="fal fa-external-link-square"></i>
              With this
            </a>
          </div>
        </td>
      </tr>
    )
  }
}

const ReportRow = connect(
  (state) => ({
    selectedBatchId: state[ REGEX_MODULE_NAME ].get('selectedBatchId'),
    selectedProjectId: state[ REGEX_MODULE_NAME ].get('selectedProjectId'),
  }),
  (dispatch) => bindActionCreators({
    changeSentenceInput,
    getReportForBatch,
    setSelectedBatchId,
    getBatchForProject,
    setSelectedProjectId,
    setActiveRootFolder,
    setActiveUrl
  }, dispatch)
)(ReportRowComponent);


const PreviewRegexPopup = ({ isOpen, title, report, onClose }) => (
  <Modal show={isOpen} bsSize="large" onHide={onClose}>

    <Modal.Header closeButton={true}>
      <Modal.Title>{title}</Modal.Title>
    </Modal.Header>

    <Modal.Body>
    <Table bordered condensed hover responsive>
      <thead>
        <tr>
          <th>Batch</th>
          <th>Regex</th>
          <th>Found</th>
          <th>Sentence</th>
          <th>Search Similar Sentences</th>
        </tr>
      </thead>
      <tbody>
      {report.size ? JSON.parse(report.get('json')||'[]').map((report, index) => (
          <ReportRow
            key={index}
            reportKey={index}
            report={report}
          />
      )) : ''}
      </tbody>
    </Table>
    </Modal.Body>

  </Modal>
);

PreviewRegexPopup.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired
};

export default PreviewRegexPopup;
