import React from "react";
import PropTypes from "prop-types";
import { Modal, Table } from "react-bootstrap";

const ReportRow = ({ report, reportKey }) =>
  <tr key={reportKey}>
    <td>{report.batch}</td>
    <td>{report.source}</td>
    <td>{report.similarity}</td>
    <td>{report.score}</td>
    <td>{report.sentence}</td>
  </tr>;

const PreviewSentencesPopup = ({ isOpen, title, report, onClose }) => (
  <Modal show={isOpen} bsSize="large" onHide={onClose}>

    <Modal.Header closeButton={true}>
      <Modal.Title>{title}</Modal.Title>
    </Modal.Header>

    <Modal.Body>
    <Table bordered condensed hover responsive>
      <thead>
        <tr>
          <th>Batch</th>
          <th>Source Sentence</th>
          <th>Similarity</th>
          <th>Score</th>
          <th>Sentence</th>
        </tr>
      </thead>
      <tbody>
      {report.size ? JSON.parse(report.get('json')||'[]').map((report, index) => {
        return(
          <ReportRow
            key={index}
            reportKey={index}
            report={report}
          />
        )
      }) : ''}
      </tbody>
    </Table>
    </Modal.Body>

  </Modal>
);

PreviewSentencesPopup.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default PreviewSentencesPopup;
