import React from 'react';
import { connect } from 'react-redux';
import {
  Accordion,
  Panel,
  Label
} from 'react-bootstrap';


const DOCUMENT_STATUS = {
  10: { text: 'Uploaded', bsClass: 'default' },
  20: { text: 'Submitted', bsClass: 'default' },
  30: { text: 'Processing', bsClass: 'info' },
  40: { text: 'Processed', bsClass: 'primary' },
  45: { text: 'Analyzed', bsClass: 'primary' },
  50: { text: 'Downloaded', bsClass: 'success' },
  55: { text: 'Deleted', bsClass: 'warning' },
  60: { text: 'Error', bsClass: 'danger' },
  undefined: { text: 'N/A', bsClass: 'default' }
};

const DOCUMENT_QUALITY = {
  1: { text: 'No OCR', bsClass: 'danger' },
  2: { text: 'Low OCR', bsClass: 'warning' },
  3: { text: 'Standard OCR', bsClass: 'primary' },
  4: { text: 'High OCR', bsClass: 'success' },
  undefined: { text: 'N/A', bsClass: 'default' }
};

const WORD_QUALITY = {
  1: { text: 'Standard Word Quality', bsClass: 'default' },
  2: { text: 'High Special Chars', bsClass: 'default' },
  3: { text: 'High Numeric Chars', bsClass: 'default' },
  undefined: { text: 'N/A', bsClass: 'default' }
};


const labelStyle = {
  marginRight: 5,
  fontSize: 10
};


const ProcessedFileListItemContent = ({ ocrStatus }) => {
  if (!ocrStatus) return <div>The file does not require OCR</div>;
  const { created_on, processed_on, status_verbose, document_quality_verbose, word_quality_verbose, message, page_count } = ocrStatus;
  return (
    <div>
      <b>Created On:</b> <span className="pull-right">{created_on}</span><br />
      <b>Processed On:</b> <span className="pull-right">{processed_on}</span><br />
      <b>Page Count:</b> <span className="pull-right">{page_count}</span><br />
      <b>Document Status:</b> <span className="pull-right">{status_verbose}</span><br />
      <b>Document Quality:</b> <span className="pull-right">{document_quality_verbose}</span><br />
      <b>Word Quality:</b> <span className="pull-right">{word_quality_verbose}</span><br />
      {message && <i>message</i>}
    </div>
  )
};

const PanelHeader = ({ fileName }) =>
  <span>
    {fileName}
  </span>;

const PanelFooter = ({ ocrStatus: { status, document_quality, word_quality } }) =>
    <div style={{ color: '#ccc' }}>
      <Label bsStyle={DOCUMENT_STATUS[status].bsClass} style={labelStyle}>
        {DOCUMENT_STATUS[ status ].text}
      </Label>
      <Label bsStyle={DOCUMENT_QUALITY[document_quality].bsClass} style={labelStyle}>
        {DOCUMENT_QUALITY[ document_quality ].text}
      </Label>
      <Label bsStyle={WORD_QUALITY[word_quality].bsClass} style={labelStyle}>
        {WORD_QUALITY[ word_quality ].text}
      </Label>
    </div>;


const ProcessedFileList = ({ processedFiles }) =>
  <Accordion className="file-list">
    {
      processedFiles.map((file, i) =>
        <Panel
          header={PanelHeader({ fileName: file.filename })}
          footer={PanelFooter({ ocrStatus: file.ocr_status || {} })}
          eventKey={i}
          key={file.id}
          className="tiny"
        >
          <ProcessedFileListItemContent ocrStatus={file.ocr_status}/>
        </Panel>
      )
    }
  </Accordion>;


export default connect(
  (state) => ({
    processedFiles: state.ocrStore.get('processedFiles')
  })
)(ProcessedFileList)
