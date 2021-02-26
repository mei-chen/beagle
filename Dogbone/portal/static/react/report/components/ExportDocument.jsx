import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import uuidV4 from 'uuid/v4';
import { ExportPopover } from 'common/components/ExportPopover'
import { bindActionCreators } from 'redux';
import {
  prepareDocumentExport,
  toggleDisplayComponentBoolean
} from 'report/redux/modules/report';

const ExportDocumentComponent = React.createClass({
  togglePopover(value) {
    const { reportActions } = this.props;
    reportActions.toggleDisplayComponentBoolean(
      'exportState',
      { showPopover: value }
    );
  },

  setLoading() {
    const { reportActions } = this.props;
    reportActions.toggleDisplayComponentBoolean(
      'exportState',
      { isLoading: true, hasError: false }
    );
  },

  resetExport() {
    const { reportActions } = this.props;
    reportActions.toggleDisplayComponentBoolean(
      'exportState',
      { hasExportIcon: true, isReady: false, hasError: false }
    );
  },


  countUnapprovedSentenceChanges() {
    const { report } = this.props;
    const analysis = report.get('analysis').toJS();
    const sentences = analysis ? analysis.sentences : [];
    // count all of the sentences which have unapproved changes
    const changedSentencesCount = (_.filter(sentences, s => s.accepted === false)).length;
    return changedSentencesCount;
  },

  hasComments() {
    const { report } = this.props;
    const analysis = report.get('analysis').toJS();
    const sentences = analysis ? analysis.sentences : [];
    return _.filter(sentences, s => s.comments_count > 0).length > 0;
  },

  hasAnnotations() {
    const { report } = this.props;
    const analysis = report.get('analysis').toJS();
    const sentences = analysis ? analysis.sentences : [];
    return _.filter(sentences, s => s.annotations !== null).length > 0;
  },

  prepareDocxExport(data={}) {
    const { reportActions } = this.props;
    reportActions.prepareDocumentExport(data);
    this.setLoading();
  },

  handleDocumentExportClick() {
    Intercom('trackUserEvent', 'export-docx');
    const { report, exportState } = this.props;

    if (exportState.isLoading) {
      return; //do nothing
    }

    if (this.countUnapprovedSentenceChanges() > 0 || this.hasComments() || this.hasAnnotations()) {
      this.togglePopover(true);
    }

    else if (report.get('uuid')!== undefined && !exportState.isReady) {
      this.setLoading();
      this.prepareDocxExport();
    }
  },

  handleDocumentExportCancel() {
    this.togglePopover(false);
  },

  renderDownloadIcon() {
    const { report, exportState } = this.props;

    if (exportState.hasError) {
      return (
        <OverlayTrigger placement="bottom" overlay={<Tooltip id={uuidV4()}>Export error</Tooltip>}>
          <i className="fa fa-exclamation-triangle download-error" />
      </OverlayTrigger>
      )
    } else {
      const url = `/api/v1/document/${report.get('uuid')}/export`;
      return (
        <OverlayTrigger placement="bottom" overlay={<Tooltip id={uuidV4()}>Download Document</Tooltip>}>
          <a href={url} onClick={() => this.resetExport()}>
            <i className="fa fa-refresh fa-cloud-download" />
            <span className="export-button-text">
              Download
            </span>
          </a>
        </OverlayTrigger>
      )
    }
  },

  renderExportIcon() {
    const { exportState } = this.props;

    if (exportState.hasExportIcon && !exportState.hasError) {
      return (
        <OverlayTrigger placement="bottom" overlay={<Tooltip id={uuidV4()}>Exporting Document</Tooltip>}>
          <span onClick={this.handleDocumentExportClick}>
            <i className="fa fa-file-word" /> Export
          </span>
        </OverlayTrigger>
      );
    }
  },

  renderIcons() {
    const { exportState } = this.props;

    //loading state or base state
    if (exportState.isLoading || (!exportState.isReady && !exportState.isLoading)) {
      const icon = (
        exportState.isLoading ?
        (<span>
          <i className="fa fa-refresh fa-spin" />
          <span className="export-button-text"> Loading.. </span>
        </span>)
        :
        (<span>
          <i className="fa fa-file-word" />
          <span className="export-button-text"> Export </span>
        </span>)
      );

      const exportTooltip = (
        exportState.isLoading ?
        <Tooltip id={uuidV4()}>Exporting Document</Tooltip> :
        <Tooltip id={uuidV4()}>Export Document as <i className="fa fa-file-word" /> Docx</Tooltip>
      );
      return (
        <OverlayTrigger placement="bottom" overlay={exportTooltip}>
          <span onClick={this.handleDocumentExportClick}>
            {icon}
          </span>
        </OverlayTrigger>
      );
    } else if (exportState.isReady) {  //ready for download state
      return (
        <span>
          { this.renderDownloadIcon() }
          &nbsp;
          { this.renderExportIcon() }
        </span>
      );
    }
  },

  render() {
    const { report ,exportState } = this.props;
    const changedSentencesCount = this.countUnapprovedSentenceChanges();
    const exportButtonClass = (this.props.extended ? 'export-button-extended' : 'export-button')
    let exportPopoverTooltip;
    if (exportState.showPopover && !exportState.isLoading) {
      exportPopoverTooltip = (
        <ExportPopover
          prepareDocxExport={this.prepareDocxExport}
          handleDocumentExportCancel={this.handleDocumentExportCancel}
          hasTrackChanges={changedSentencesCount > 0}
          hasComments={this.hasComments()}
          setLoading={this.setLoading}
          uuid={report.get('uuid')}
          report_style={true}
        />
      );
    }

    return (
      <div className={exportButtonClass}>
        { this.renderIcons() }
        {exportPopoverTooltip}
      </div>
    );
  }

});

const mapExportDocumentComponentStateToProps = (state) => {
  return {
    report: state.report,
    exportState: state.report.get('exportState')
  }
};

function mapExportDocumentComponentDispatchToProps(dispatch) {
  return {
    reportActions: bindActionCreators({
      prepareDocumentExport,
      toggleDisplayComponentBoolean
    }, dispatch)
  };
}

export default connect(
  mapExportDocumentComponentStateToProps,
  mapExportDocumentComponentDispatchToProps
)(ExportDocumentComponent)
