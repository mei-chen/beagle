var React = require('react');
var Reflux = require('reflux');
var $ = require('jquery');
import _ from 'lodash';
var Button = require('react-bootstrap/lib/Button');
var io = require('socket.io-client');
var socket = io(window.socketServerAddr);
var log = require('utils/logging');
var Popover = require('react-bootstrap/lib/Popover');
var Tooltip = require('react-bootstrap/lib/Tooltip');
var Timestamp = require('react-time');
var classNames = require('classnames');
var ButtonToolbar = require('react-bootstrap/lib/ButtonToolbar');
var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');
var { Navigation } = require('react-router');

var ReportStore = require('report/stores/ReportStore');
var { ReportActions } = require('report/actions');
var UserStore = require('common/stores/UserStore');
var { Notification } = require('common/actions');
var fileDownload = require('utils/fileDownload');

require('report/components/styles/DocumentSummary.scss');
require('./styles/DocumentSummary.scss');


var UnconfirmedChangesPopover = React.createClass({

  mixins: [Navigation],

  handleExportAnyways() {
    this.props.setLoading();
    this.props.prepareDocxExport();
    this.props.handleDocumentExportCancel();
  },

  sendToModal() {
    this.props.handleDocumentExportCancel();
    this.transitionTo('/context-view');
  },

  render() {
    var plural = this.props.changedSentencesCount > 1 ? { verb:"are", change:"changes"} : {verb:"is", change:"change"};
    var dialog = (
      <span>
        We have detected there {plural.verb}
        <strong> {this.props.changedSentencesCount} </strong>
        unconfirmed {plural.change}.
        Either accept them <a onClick={this.sendToModal}>here</a>, or
      </span>
    );
    var title = 'Add extras';

    return (
      <div className="beagle-topbar">
        <div className="popup-overlay" onClick={this.props.handleDocumentExportCancel} />
        <Popover placement='bottom' positionTop="100%"
          positionLeft={-113} title={title} id='document-export-popover'>
          <div className="dialog">
            {dialog}
          </div>
          <ButtonToolbar>
            <Button bsStyle='info' onClick={this.handleExportAnyways}>Export</Button>
            <Button onClick={this.props.handleDocumentExportCancel}>Cancel</Button>
          </ButtonToolbar>
        </Popover>
      </div>
    );
  }

});


var ExportDocument = React.createClass({

  propTypes: {
    analysis: React.PropTypes.object.isRequired,
  },

  getInitialState() {
    return {
      analysis: this.props.analysis,
      isClicked: false,
      showPopover: false,
      isLoading: false,
      isReady: false,
      docUUID: null
    }
  },

  componentDidMount() {
    this.socketListener();
    var uuid = this.state.analysis.uuid;
    this.setState({ docUUID : uuid });
  },

  socketListener() {
    socket.on('message', msg => {
      log('msg received', msg);
      var type = msg.notif;

      if (
        msg.document && msg.document.uuid &&
        this.state.docUUID !== msg.document.uuid
      ) {
        return; // do nothing
      }

      else if (type === 'DOCUMENT_EXPORT_READY') {
        this.hideLoading();
        this.setReady();
      }

      else if (type === 'DOCUMENT_CHANGED' && this.state.isReady ) {
        this.hideReady();
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


  countUnapprovedSentenceChanges() {
    var analysis = this.state.analysis.analysis;
    var sentences = analysis ? analysis.sentences : [];
    // count all of the sentences which have unapproved changes
    var changedSentencesCount = (_.filter(sentences, s => s.accepted === false)).length;
    return changedSentencesCount;
  },

  prepareDocxExport() {
    let analysis = this.state.analysis;
    let url = `/api/v1/document/${analysis.uuid}/prepare_export`;
    $.post(url);
    this.setLoading();
  },

  handleDocumentExportClick() {
    Intercom('trackUserEvent', 'export-docx');
    var analysis = this.state.analysis;

    if (this.state.isLoading) {
      return; //do nothing
    }

    if (this.countUnapprovedSentenceChanges() > 0) {
      this.showPopover();
    }
    else if (analysis.uuid !== undefined && this.state.isReady === false) {
      this.setLoading();
      this.prepareDocxExport();
    }
  },

  handleDocumentExportCancel() {
    this.hidePopover();
  },

  render() {
    var analysis = this.state.analysis;
    var changedSentencesCount = this.countUnapprovedSentenceChanges();

    var unconfirmedChangesPopover;
    if (this.state.showPopover && !this.state.isLoading) {
      unconfirmedChangesPopover = (
        <UnconfirmedChangesPopover
          prepareDocxExport={this.prepareDocxExport}
          handleDocumentExportCancel={this.handleDocumentExportCancel}
          changedSentencesCount={changedSentencesCount}
          setLoading={this.setLoading}/>
      );
    }

    var iconSpan;
    var exportTooltip;
    //loading state or base state
    if (this.state.isLoading || (!this.state.isReady && !this.state.isLoading)) {
      var icon = this.state.isLoading ? <i className="fa fa-refresh fa-spin"></i> : <i className="fa fa-file-word-o"></i>;
      iconSpan = (
          <span onClick={this.handleDocumentExportClick}>
            {icon}
          </span>);
      exportTooltip = this.state.isLoading ? <Tooltip>Exporting Document</Tooltip> : <Tooltip>Export Document as <i className="fa fa-file-word-o"></i> Docx</Tooltip>;
    }
    //ready for download state
    else if (this.state.isReady) {
      let analysis = this.state.analysis;
      let url = `/api/v1/document/${analysis.uuid}/export`;
      iconSpan = (
          <a href={url}>
            <i className="fa fa-refresh fa-cloud-download"></i>
          </a>);
      exportTooltip = <Tooltip>Download Document</Tooltip>;
    }


    return (
      <div className='export-button'>
        <OverlayTrigger placement='bottom' overlay={exportTooltip}>
          {iconSpan}
        </OverlayTrigger>
        {unconfirmedChangesPopover}
      </div>
    );
  }

});


var InplaceEditParty = React.createClass({

  _sendChange(ev) {
    this.props.onPartyChange(this.props.id, ev.target.value);
  },

  render() {
    var party = this.props.party;

    var confidenceTooltip = (party.confidence <= 100) ? (
      <Tooltip><strong>{party.confidence}% Confidence</strong></Tooltip>
    ) : (
      <Tooltip><strong>Manually set</strong></Tooltip>
    );

    var confidlineStyle = {
      width: Math.min(party.confidence, 100) + "%"
    }

    var inputClasses = classNames(
      'party_name',
      'party_edit'
    );
    var spanClasses = classNames(
      'party_name',
      'party_nonedit',
    );

    var container;
    if (this.props.editMode) {
      container = (
        <div className="header-party">
          <input id={this.props.id} ref="partyspan" className={inputClasses}
                 onChange={this._sendChange} value={party.name} />
        </div>
      );
    } else {
      container = (
        <OverlayTrigger placement="bottom" overlay={confidenceTooltip}>
          <div className="header-party">
            <span id={this.props.id} ref="partyspan" className={spanClasses}>
              {party.name}
            </span>
            <div className='confid-bg'>
              <div className='confid-line' style={confidlineStyle}></div>
            </div>
          </div>
        </OverlayTrigger>
      );
    }

    return (
      <span>
            {container}
      </span>
    );
  }
});


var InplaceEditButton = React.createClass({

  propTypes : {
    uuid : React.PropTypes.string
  },

  getInitialState() {
    return {
      showUnconfidentPopover : false
    };
  },

  componentDidMount() {
    this.socketListener();
    var uuid = this.props.uuid;
    this.setState({ docUUID : uuid });
  },

  socketListener() {
    socket.on('message', msg => {
      log('msg received', msg);
      var type = msg.notif;

      if (
        msg.document && msg.document.uuid &&
        this.state.docUUID !== msg.document.uuid
      ) {
        return; // do nothing
      }

      //If the WEAK_DOCUMENT_ANALYSIS notification comes, show the user how to set the
      // parties manually
      else if (type === 'WEAK_DOCUMENT_ANALYSIS') {
        this.setShowUnconfidentPopover();
      }
    });
  },

  _onSubmit(event) {
    this.props.submitFn();
  },

  _onDiscard(event) {
    this.props.discardFn();
  },

  _onEdit(event) {
    this.props.onEdit();
    this.clearShowUnconfidentPopover();
  },

  setShowUnconfidentPopover() {
    this.setState({ showUnconfidentPopover : true });
  },

  clearShowUnconfidentPopover() {
    this.setState({ showUnconfidentPopover : false });
  },

  generateWeakAnalysisPopover() {
    if (this.state.showUnconfidentPopover) {
      return (
          <Popover placement='bottom' positionTop="100%"
            positionLeft={-111}
            title="Uh Oh!"
            id='document-export-popover'>
            <i className="fa fa-close close-weak-analysis-popover" onClick={this.clearShowUnconfidentPopover}/>
          Beagle can’t seem to figure out the parties with great confidence.  Click here to set them manually and we’ll reanalyze the agreement.
          </Popover>
      );
    } else {
      return null
    }
  },

  render() {
    var editMode = this.props.editMode;
    var changed = this.props.changed;
    var buttonClasses = classNames(
      'small-button',
    );

    var editPartiesTooltip = (
      <Tooltip><strong>Edit parties</strong></Tooltip>
    );

    if (editMode || changed) {
      return (
        <span>
          <Button bsStyle="success" onClick={this._onSubmit} className={buttonClasses}>
            Re-analyze
          </Button>
          <Button bsStyle="default" onClick={this._onDiscard} className={buttonClasses}>
            <i className="fa fa-times"></i>
          </Button>
        </span>
      );
    } else {
      return (
        <span className="inplace-edit-parties-button">
          <OverlayTrigger placement="bottom" overlay={editPartiesTooltip}>
            <button onClick={this._onEdit} className="subtle-button">
              <i className="fa fa-pencil-square-o"></i>
            </button>
          </OverlayTrigger>
          {this.generateWeakAnalysisPopover()}
        </span>
      );
    }
  }

});


var InplacePartiesFlipButton = React.createClass({

  _onClick(event) {
    this.props.onFlip();
  },

  render() {
    var content;
    if (this.props.editMode) {
      content = (
        <button className="subtle-button" onClick={this._onClick}>
          <i className="fa fa-exchange"></i>
        </button>
      );
    } else {
      content = 'and'
    }

    return (
      <span>
        {content}
      </span>
    );
  }
});


var InplaceEditForm = React.createClass({

  propTypes: {
    analysis: React.PropTypes.object.isRequired,
  },

  getInitialState() {
    return {
      analysis: this.props.analysis,
      editmode: false,
      changed: false,
      partyY: this.props.parties.you,
      partyT: this.props.parties.them,
      origPartyY: {...this.props.parties.you},
      origPartyT: {...this.props.parties.them},
    };
  },

  onEditRequest() {
    if (!this.state.editmode) {
      this.setState({editmode: true});
    }
  },

  onEditOffRequest() {
    if (this.state.editmode) {
      this.setState({editmode: false});
    }
  },

  formSubmit() {
    // Gather new parties and send request
    var self = this;
    var uuid = this.state.analysis.uuid;
    var url = `/api/v1/document/${uuid}/parties`;
    $.post(url, JSON.stringify({
      parties: [
        this.state.partyY.name,
        this.state.partyT.name
      ]
    })).done((data) => {
      // Trigger reanalysis
      ReportActions.refreshAnalysis();
      // Hide the editing form
      self.setState({
        changed: false,
        editmode: false
      });
    });
  },

  formDiscard() {
    // Hide the editing form
    this.setState({
      changed: false,
      editmode: false
    });
    this.setState({
      partyY: {...this.state.origPartyY},
      partyT: {...this.state.origPartyT}
    });
  },

  flipParties() {
    this.setState({changed: true});

    this.setState({partyY: this.state.partyT,
                   partyT: this.state.partyY});
  },

  onPartyChange(id, name) {
    var modif_party;
    this.setState({changed: true});
    if (id == 'partya') {
      modif_party = this.state.partyY;
      modif_party.name = name;
      this.setState({partyY: modif_party});
    } else {
      modif_party = this.state.partyT;
      modif_party.name = name;
      this.setState({partyT: modif_party});
    }
  },

  render() {
    // Disable the InplaceEditButton if the user isn't the owner
    var isOwner = ReportStore.isOwner();
    var inplaceEditButton = isOwner ? (<InplaceEditButton editMode={this.state.editmode}
                                                          changed={this.state.changed}
                                                          onEdit={this.onEditRequest}
                                                          discardFn={this.formDiscard}
                                                          submitFn={this.formSubmit}
                                                          uuid={this.state.analysis.uuid}/>) : null;

    return (
      <span className="parties">
        <InplaceEditParty id="partya" party={this.state.partyY} ref="youPartyNode"
                          editMode={this.state.editmode}
                          onEdit={this.onEditRequest} onEditOff={this.onEditOffRequest}
                          onPartyChange={this.onPartyChange} changed={this.state.changed} />

        <InplacePartiesFlipButton editMode={this.state.editmode} onFlip={this.flipParties} />

        <InplaceEditParty id="partyb" party={this.state.partyT} ref="themPartyNode"
                          editMode={this.state.editmode}
                          onEdit={this.onEditRequest} onEditOff={this.onEditOffRequest}
                          onPartyChange={this.onPartyChange} changed={this.state.changed} />
        {inplaceEditButton}
      </span>
    );
  }
});


var DocumentSummary = React.createClass({

  propTypes: {
    analysis: React.PropTypes.object.isRequired,
  },

  render() {
    var analysis = this.props.analysis;
    if (!analysis) {
      return null;
    }

    var documentName;
    var documentType, documentTypeConfidence;
    var parties;
    var content;
    var article;
    var uploadedTime;

    documentName = analysis.title;
    parties = analysis.analysis.parties;
    documentType = analysis.agreement_type || 'Agreement';
    documentTypeConfidence = Math.round(analysis.agreement_type_confidence * 100);
    article = documentType[0] == 'A' ? 'an' : 'a';
    uploadedTime = (
      <Timestamp
        value={analysis.created}
        locale="en"
        format="MMMM DD, YYYY hh:mm a" />
    );

    var doctypeTooltip = (
      <Tooltip>{documentTypeConfidence}% confidence</Tooltip>
    );

    return(
      <div className="beagle-document-summary">
        <div className="summary-topbar">
          <h1 className="summary-title">{documentName}</h1>
          <div className="parties">
            This is {article}:&nbsp;&nbsp;
            <OverlayTrigger placement="bottom" overlay={doctypeTooltip}>
              <span id="doctype">{documentType}</span>
            </OverlayTrigger>
            &nbsp;&nbsp;between
            <InplaceEditForm
              analysis={analysis}
              parties={parties}
            />
          </div>
          <ExportDocument
            analysis={analysis}
          />
        </div>
        <div className="uploaded-time">Uploaded on {uploadedTime}</div>
      </div>
    );
  }

});


module.exports = DocumentSummary;
