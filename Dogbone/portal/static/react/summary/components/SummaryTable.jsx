import React from 'react';
import { connect } from 'react-redux';
import Spinner from '../../report/components/Spinner';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

require('./styles/SummaryTable.scss');

var SummaryTable = React.createClass({

  render() {
    const { documents, isInitialized } = this.props;
    const files = documents.toJS();
    const isLoaded = files && files.length !== 0;

    if (!isInitialized || !isLoaded) {
      return (
        <div id="step2">
          <div className="loading">
            <Spinner inline /> Your document is being analyzed
          </div>
        </div>
      );
    }

    const listOfFiles = files.map((file, key) => {

      const errorIcon = file.error ?
        (<OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">{file.error}</Tooltip>}>
          <i className="fa fa-exclamation-triangle" aria-hidden="true"></i>
        </OverlayTrigger>) : undefined ;

      return (
        <div className="top-row document-row" key={key}>
          <div className="row-cell doc-title"><a title={file.title} href={file.url+(this.props.defaultRepView || '')}>{file.title}</a></div>
          <div className="row-cell">{file.type}</div>
          <div className="row-cell">{file.uploaded}</div>
          <div className="row-cell">{file.company || '-'}</div>
          <div className="handshake"/>
          <div className="row-cell">{file.contractor || '-'}</div>
          <div className="row-cell error">{errorIcon}</div>
        </div>
      )
    })
    return (
      <span>
        <div className="table-container top">
          <div className="top-row top">
            <div className="row-cell doc-title"><i className="fa fa-file-word" aria-hidden="true"/> Document name</div>
            <div className="separator"/>
            <div className="row-cell"><i className="fa fa-file-alt" aria-hidden="true"/> Document type</div>
            <div className="separator"/>
            <div className="row-cell"><i className="fa fa-clock" aria-hidden="true"/> Processing time</div>
            <div className="separator"/>
            <div className="row-cell">Party A</div>
            <i className="fa fa-handshake" aria-hidden="true"/>
            <div className="row-cell">Party B</div>
            {/*<div className="row-cell"><i className="fa fa-exclamation-triangle" aria-hidden="true"/> Upload error</div>*/}
          </div>
        </div>
        <div className="top-row-separator name"/>
        <div className="top-row-separator type"/>
        <div className="top-row-separator time"/>
        <div className="top-row-separator partys"/>
        <div className="table-container">
          {listOfFiles}
        </div>
      </span>
    )
  }
})

const mapStateToProps = (state) => {
  return {
    defaultRepView: state.setting.get('default_report_view'),
    documents: state.summary.get('documents'),
    isInitialized: state.summary.get('isInitialized')
  }
};

export default connect(mapStateToProps)(SummaryTable)
