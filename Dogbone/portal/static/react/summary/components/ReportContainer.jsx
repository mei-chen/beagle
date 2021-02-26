import React from 'react';
import { connect } from 'react-redux';
import io from 'socket.io-client';
import log from 'utils/logging';
import Popover from 'react-bootstrap/lib/Popover';
import ButtonToolbar from 'react-bootstrap/lib/ButtonToolbar';
import Checkbox from 'react-bootstrap/lib/Checkbox';
import Button from 'react-bootstrap/lib/Button';
import {
  exportBatch,
} from 'account/redux/modules/project';
import {
  getFromServer as getData
} from '../redux/modules/summary';
const socket = io(window.socketServerAddr);

//App
import SummaryTable from './SummaryTable';

require('./styles/ReportContainer.scss');

const UnconfirmedChangesPopover = React.createClass({

  getInitialState() {
    this.annotationsThatAreIncluded={};
    return {
      includeAnnotations:false,
      annotations:[]
    }
  },

  showDropdown() {
    this.setState({ includeAnnotations: !this.state.includeAnnotations });
    this.getAnnotations();
  },

  passAnnotations(annotations) {
    if (this.state.annotations !== annotations)
      this.setState({ annotations: annotations });
  },

  handleExportAnyways() {
    var data;
    data = {
      include_track_changes: this.includeTrackChanges.checked,
      include_comments: this.includeComments.checked,
      include_annotations: this.includeAnnotations.checked,
    };

    this.props.setLoading();
    this.props.prepareDocxExport(data);
    this.props.handleDocumentExportCancel(data);
  },

  render() {
    const dialog = (
     <span>
        <Checkbox
          inputRef={ref => { this.includeTrackChanges = ref; }}
          disabled={!(this.props.hasTrackChanges>0)}>
          Include track-changes
        </Checkbox>

        <Checkbox
          inputRef={ref => { this.includeComments = ref; }}
          disabled={!this.props.hasComments}>
          Include comments
        </Checkbox>

        <Checkbox
          inputRef={ref => { this.includeAnnotations = ref; }}>
          Include Beagle annotations
        </Checkbox>
      </span>
    );
    const title = 'Add extras';

    return (
      <span className="popover-tooltip">
        <div className="popup-overlay" onClick={this.props.handleDocumentExportCancel} />
        <Popover id="document-export-popover" placement="bottom" title={title} className="document-export-popover" style={{ width:'100%' }}>
          <div className="dialog">
            {dialog}
          </div>
          <ButtonToolbar>
            <Button bsStyle="info" onClick={this.handleExportAnyways}>Export</Button>
            <Button onClick={this.props.handleDocumentExportCancel}>Cancel</Button>
          </ButtonToolbar>
        </Popover>
      </span>
    );
  }
});

const ExportBatch = React.createClass({

  getInitialState() {
    return {
      isClicked: false,
      showPopover: false,
      isLoading: false,
      isReady: false,
      docUUID: null
    }
  },

  componentWillMount() {
    this.setState({ batchId : this.props.batch_id });
  },

  componentDidMount() {
    this.socketListener();
  },

  socketListener() {
    socket.on('message', msg => {
      log('msg received', msg);
      var type = msg.notif;

      if (
        !msg.batch
      ) {
        return; // do nothing
      }

      else if (type === 'BATCH_WAS_PREPARED') {
        this.hideLoading();
        this.setReady();
      }
    });
  },

  showPopover() {
    this.setState({
      showPopover: true,
    });
  },

  hidePopover() {
    this.setState({
      showPopover: false,
    });
  },

  setLoading() {
    this.setState({
      isLoading: true
    });
  },

  hideLoading() {
    this.setState({
      isLoading: false
    });
  },

  setReady() {
    this.setState({
      isReady: true
    });
  },

  hideReady() {
    this.setState({
      isReady: false
    });
  },

  prepareDocxExport(params) {
    const { dispatch } = this.props;
    dispatch(exportBatch(this.props.batch_id, params))
    this.setLoading();
  },

  handleDocumentExportClick() {
    if (this.state.isLoading) {
      return; //do nothing
    }

    this.showPopover();
  },

  hasComments() {
    return this.props.docstats.comments>0
  },

  handleDocumentExportCancel() {
    this.hidePopover();
  },

  render() {
    var unconfirmedChangesPopover;
    if (this.state.showPopover && !this.state.isLoading) {
      unconfirmedChangesPopover = (
        <UnconfirmedChangesPopover
          prepareDocxExport={this.prepareDocxExport}
          handleDocumentExportCancel={this.handleDocumentExportCancel}
          hasComments={this.hasComments()}
          hasTrackChanges={this.props.docstats.redlines}
          batch={this.props.batch_id}
          setLoading={this.setLoading}
          url={this.props.url}
        />
      );
    }

    var iconSpan;
    // var exportTooltip;

    //loading state or base state
    if (this.state.isLoading || (!this.state.isReady && !this.state.isLoading)) {
      var icon = this.state.isLoading ? <i className="fa fa-sync fa-spin" /> : <i className="fa fa-file-word" />;
      iconSpan = (
        <span className="extra-tool-wrapper">
          <span onClick={this.handleDocumentExportClick}>
            <span className="export-button">
              {icon}
              docx
            </span>
          </span>
          {unconfirmedChangesPopover}
        </span>
      );
      // exportTooltip = this.state.isLoading ? <Tooltip id="tooltip-top">Exporting Document</Tooltip> : <Tooltip id="tooltip-top">Export Document as <i className="fa fa-file-word" /> Docx</Tooltip>;
    }
    //ready for download state
    else if (this.state.isReady) {
      let url = `/api/v1/batch/${this.props.batch_id}/export`;
      iconSpan = (
        <span className="extra-tool-wrapper">
          <span>
            <a className="export-button" href={url}>
              <i className="fa fa-cloud-download" />
              docx
            </a>
          </span>
          {unconfirmedChangesPopover}
        </span>
      );
      // exportTooltip = <Tooltip id="tooltip-top">Download Document</Tooltip>;
    }


    return (
      <span>
        {iconSpan}
      </span>
    );
  }
});

var ReportContainer = React.createClass({
  componentWillMount() {
    const { dispatch } = this.props;
    dispatch(getData());
  },

  render() {
    const exportButton = (
      <div className="export-buttons">
          <ExportBatch
            batch_id={this.props.batch_id}
            dispatch={this.props.dispatch}
            docstats={this.props.docstats}
            />

        <a className="export-button" href={`/api/v1/batch/${this.props.batch_id}/export_summary`}>
          <i className="fa fa-file" />
          csv
        </a>
      </div>
    );

    return (
      <div className="report-wrap-container">
        {exportButton}
        <h1 className="report-title">{this.props.batch_title}</h1>
        <SummaryTable/>
      </div>
    )
  }
})

const mapStateToProps = (state) => {
  return {
    analyzed: state.summary.get('analyzed'),
    batch_id: state.summary.get('batch_id'),
    batch_title: state.summary.get('upload_title'),
    docstats: state.summary.get('docstats').toJS(),
  }
};

export default connect(mapStateToProps)(ReportContainer)
