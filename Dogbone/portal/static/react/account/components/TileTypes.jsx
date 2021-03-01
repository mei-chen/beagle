import React from 'react';
import { connect } from 'react-redux';
import $ from 'jquery';
import io from 'socket.io-client';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import Time from 'react-time';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import { ExportPopover, ExportBatchPopover } from 'common/components/ExportPopover';

// App
import log from 'utils/logging';
import { SharedUsersProject } from 'report/components/SharedUsers';
import {
  exportBatch,
  exportDocument,
  getDocumentDetails
} from '../redux/modules/project';

require('./styles/ProjectTiles.scss');

const socket = io(window.socketServerAddr);

const DEFAULT_AGREEMENT_TYPE = 'Agreement';

const Stat = React.createClass({
  render() {
    const { title, value, iconClass } = this.props;

    return (
      <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">{ title }</Tooltip>}>
        <div className={`info-icon ${value == 0 ? 'none' : ''}`}>
          <i className={iconClass} />
          <div className={`alerts ${value == 0 ? 'none' : ''}`}>
            {(value > 99) ? <span className="over-flow">99+</span> : <span>{ value }</span>}
          </div>
        </div>
      </OverlayTrigger>
    )
  }
})

const ExportDocumentComponent = React.createClass({

  getInitialState() {
    return {
      isClicked: false,
      showPopover: false,
      isLoading: false,
      isReady: false,
      docId: null,
    }
  },

  componentWillMount() {
    this.socketListener();
  },

  socketListener() {
    socket.on('message', msg => {
      log('msg received', msg);
      var type = msg.notif;

      if (
        msg.document && msg.document.uuid &&
        this.props.docId !== msg.document.uuid) {
        return; // do nothing
      }

      else if (type === 'DOCUMENT_EXPORT_READY' || type === 'BATCH_WAS_PREPARED') {
        this.hideLoading();
        this.setReady();
      }

      else if (type === 'DOCUMENT_CHANGED' && this.state.isReady) {
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
    return this.props.redlines;
  },

  hasComments() {
    return this.props.nrComments>0 ? true : false
  },

  prepareDocxExport(data) {
    const { dispatch, isBatch } = this.props;
    dispatch(isBatch ? exportBatch(this.props.docId, data) : exportDocument(this.props.docId, data));
    this.setLoading();
  },

  handleDocumentExportClick() {
    if (this.state.isLoading) {
      return; //do nothing
    }

    this.showPopover();
  },

  handleDocumentExportCancel() {
    this.hidePopover();
  },

  render() {
    var changedSentencesCount = this.countUnapprovedSentenceChanges();

    var selectExportInclusionsPopover;
    if (this.state.showPopover && !this.state.isLoading) {
      selectExportInclusionsPopover = (this.props.isBatch ?
        (<ExportBatchPopover
          prepareDocxExport={this.prepareDocxExport}
          handleDocumentExportCancel={this.handleDocumentExportCancel}
          hasComments={this.hasComments()}
          changedSentencesCount={changedSentencesCount}
          setLoading={this.setLoading}
          batch={this.props.docId}
          account_style={true}
        />) :
        (<ExportPopover
          prepareDocxExport={this.prepareDocxExport}
          handleDocumentExportCancel={this.handleDocumentExportCancel}
          hasTrackChanges={changedSentencesCount}
          hasComments={this.hasComments()}
          setLoading={this.setLoading}
          uuid={this.props.docId}
          account_style={true}
        />)
      );
    }

    var iconSpan;

    //loading state or base state
    if (this.state.isLoading || (!this.state.isReady && !this.state.isLoading)) {
      var icon = this.state.isLoading ? <i className="fa fa-sync fa-spin fa-fw" /> : <i className="fa fa-file-word" />;
      iconSpan = (
        <span>
          <div className="extra-tool-wrapper" onClick={this.handleDocumentExportClick}>
            <span>
              {icon}
            </span>
            <div className="extra-tool-text">
              {this.props.isBatch ? 'Export batch' : 'Export document'}
            </div>
          </div>
          {selectExportInclusionsPopover}
        </span>
      );
    }
    //ready for download state
    else if (this.state.isReady) {
      const url = (this.props.isBatch ? `/api/v1/batch/${this.props.docId}/export` : `/api/v1/document/${this.props.docId}/export`);
      iconSpan = (
        <span>
          <div className="extra-tool-wrapper">
            <a href={url}>
              <i className="fa fa-refresh fa-cloud-download" />
              <div className="extra-tool-text">
                {this.props.isBatch ? 'Download batch' : 'Download document'}
              </div>
            </a>
          </div>
          {selectExportInclusionsPopover}
        </span>
      );
    }

    return (
      <span>
        {iconSpan}
      </span>
    );
  }
});

const ExportDocument = connect()(ExportDocumentComponent);

const SingularDocumentTileComponent = React.createClass({
  getInitialState() {
    return {
      document: null,
      docstats: null,
      isActive: false,
      isLoading: false
    };
  },

  onCollapseClick() {
    const { isActive, document } = this.state;
    const { batchId, uuid, isOwner, dispatch } = this.props;

    // if open
    if (isActive) return this.setState({ isActive: false });

    // if closed with existing data
    if (document) {
      return this.setState({ isActive: true })

    // if closed with no data
    } else {
      this.setState({ isLoading: true, isActive: true });
      dispatch(getDocumentDetails(isOwner ? { batchId } : { uuid }))
        .then(res => {
          const { documents, docstats } = res.data;
          const document = isOwner ? documents[0] : res.data;
          this.setState({ isLoading: false, document, docstats })
        })
        .catch(() => this.setState({ isLoading: false }))
    }
  },

  onTrashClick() {
    const { title, batchId, openDeleteModal } = this.props;

    openDeleteModal({ batch: false, title, batch_id: batchId }, this.onCollapseClick);
  },

  onRejectClick() {
    const { uuid, title, openRejectModal } = this.props;

    openRejectModal({ batch: false, title, uuid }, this.onCollapseClick);
  },

  renderDropContent() {
    const { isLoading, document, docstats } = this.state;

    // if loading
    if (isLoading) return <div className="tile-loader"><i className="fa fa-cog fa-spin" /></div>;

    // if error
    if (!document) return <div className="tile-fetch-error">Error while fetching data</div>;

    const { uuid, isOwner, owner, title, reportUrl } = this.props;
    const { collaborators } = document;
    const { redlines, comments, suggested, keywords } = docstats;

    const docTools = (
      <div className="tile-tools">
        <ExportDocument
          docId={uuid}
          url={reportUrl}
          redlines={redlines}
          nrComments={comments}
        />
        { isOwner ? (
          <span onClick={this.onTrashClick} className="delete-icon">
            <i className="fa fa-trash"/>
            <div className="delete-text">Delete</div>
          </span>
        ) : (
          <span onClick={this.onRejectClick} className="delete-icon">
            <i className="fa fa-trash"/>
            <div className="delete-text">Reject</div>
          </span>
        ) }
      </div>
    );

    const docStats = (
      <div className="doc-stats">
        <Stat title="Changes" iconClass="fa fa-clock" value={redlines} />
        <Stat title="Comments" iconClass="fa fa-comment" value={comments} />
        <Stat title="Learners" iconClass="fa fa-lightbulb" value={suggested} />
        <Stat title="Keywords" iconClass="fa fa-bookmark" value={keywords} />
      </div>
    );

    const sharedUsersContainer = (
      <div className="tile-shared-users">
        <SharedUsersProject
          uuid={uuid}
          documentName={title}
          isOwner={isOwner}
          owner={owner}
          collaborators={collaborators} />
      </div>
    );

    return (
      <div>
        { docStats }
        { sharedUsersContainer }
        { docTools }
      </div>
    )
  },

  render() {
    const { isActive } = this.state;
    const {
      isOwner,
      defaultRepView,
      agreementType,
      title,
      username,
      image,
      created,
      parties: { you, them },
      reportUrl
    } = this.props;

    const projectURL = `${reportUrl}${defaultRepView || ''}`;

    const tileImage = (
      <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Owner: {username}</Tooltip>}>
        <img className="owner-avatar" src={image}/>
      </OverlayTrigger>
    );

    const tileTitle = (
      <div className="project-title">
        <div className="project-type">
          { agreementType || DEFAULT_AGREEMENT_TYPE }
        </div>
        <div className="project-name-wrapper">
          <a
            className={`project-link ${!isOwner ? 'invited' : ''}`}
            href={projectURL}
            title={title}>
            {title}
          </a>
        </div>
      </div>
    );

    const tileUploaded = !isActive ? null : (
      <div className="date-uploaded-container">
        <Time locale="en"
          value={created} format="MMMM DD, YYYY hh:mm a" />
      </div>
    );

    const tileParties = (
      <div className={`party-wrapper ${isActive ? 'open' : ''}`}>
        <div className="party-info" title={you.name}>
          <span className="party-name">
            <i className="fa fa-user"/> {you.name}
          </span>
          { isActive && (
            <span className="confidence">
              { you.confidence > 100 ? 'Manually set' : you.confidence + '% Confidence' }
            </span>
          ) }
        </div>
        <div className="party-info" title={them.name}>
          <span className="party-name">
            <i className="fa fa-building"/> {them.name}
          </span>
          { isActive && (
            <span className="confidence">
              { them.confidence > 100 ? 'Manually set' : them.confidence + '% Confidence' }
            </span>
          ) }
        </div>
      </div>
    );

    const tileCollapseBtn = (
      <span onClick={this.onCollapseClick}>
        <div className="tile-trigger">
          <div className="arrow-container">
            <i className={`fa fa-chevron-${isActive ? 'up' : 'down'} expand-icon`}/>
          </div>
        </div>
      </span>
    );

    return (
      <div className={`project-tile ${isActive ? 'open' : 'closed'}`}>
        <div className="tile-header">
          { tileImage }
          { tileTitle }
        </div>

        <div className="tile-body">
          { tileUploaded }
          { tileParties }
          { isActive && this.renderDropContent() }
          { tileCollapseBtn }
        </div>
      </div>
    );
  }
});

export const SingularDocumentTile = connect()(SingularDocumentTileComponent);

export const PendingTileComponent = React.createClass({
  render() {
    const {
      isBatch,
      defaultRepView,
      title,
      image,
      username,
      isOwner,
      reportUrl } = this.props;

    const projectURL = isBatch ? undefined : `${reportUrl}${defaultRepView || ''}`;

    const tileImage = (
      <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Owner: { username }</Tooltip>}>
        <img className="owner-avatar" src={image}/>
      </OverlayTrigger>
    );

    const tileTitle = (
      <div className="project-title">
        { isBatch && <div className="project-type batch">Batch</div> }
        <div className="project-name-wrapper">
          <a
            className={`project-link ${!isOwner ? 'invited' : ''}`}
            href={projectURL}
            title={title}>
            {title}
          </a>
        </div>
      </div>
    );

    const headerColor = {
      borderColor: isOwner ? '#5D101A' : '#147039',
      backgroundColor: '#fafafa'
    };

    return (
      <div className="project-tile closed">
        <div className="tile-header pending" style={headerColor}>
          { tileImage }
          { tileTitle }
        </div>

        <div className="tile-body">
          <div className = "spinner">
            <i className="fa fa-spinner fa-spin" /> Processing
          </div>
        </div>
      </div>
    );
  }
})

export const FailedTileComponent = React.createClass({
  getInitialState() {
    return {
      isActive: false
    };
  },

  onCollapseClick() {
    this.setState({ isActive: !this.state.isActive });
  },

  onRetryClick() {
    const { uuid } = this.props;
    const url = `/api/v1/document/${uuid}/reanalysis`;

    $.post(url).done(this.onCollapseClick);
  },

  onTrashClick() {
    const { uuid, batchId, isOwner, title, openRejectModal, openDeleteModal } = this.props;

    if (!isOwner)
      openRejectModal({ batch: false, title, uuid }, this.onCollapseClick);
    else
      openDeleteModal({ batch: false, title, batch_id: batchId }, this.onCollapseClick);
  },

  renderDropContent() {
    const { isBatch, isOwner, detailedErrorMessage } = this.props;

    const errorMessageContent = <div className="error-message-detailed-wrapper">{ detailedErrorMessage }</div>;

    const docTools = (
      <div className="tile-tools">
        { isOwner && !isBatch && (
          <span onClick={this.onRetryClick} className="extra-tool-wrapper">
            <i className="fa fa-repeat" />
            <div className="extra-tool-text">Re-analyze</div>
          </span>
        ) }
        <span onClick={this.onTrashClick} className="delete-icon">
          <i className="fa fa-trash"/>
          <div className="delete-text">
            {isOwner ? 'Delete' : 'Reject'}
          </div>
        </span>
      </div>
    );

    return (
      <div>
        { errorMessageContent }
        { docTools }
      </div>
    )
  },

  render() {
    const { isBatch, title, username, image, errorMessage } = this.props;
    const { isActive } = this.state;

    const tileImage = (
      <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Owner: { username }</Tooltip>}>
        <img className="owner-avatar" src={image}/>
      </OverlayTrigger>
    );

    const tileTitle = (
      <div className="project-title">
        { isBatch && <div className="project-type batch">Batch</div> }
        <div className="project-name-wrapper">{ title }</div>
      </div>
    );

    const tileCollapseBtn = (
      <span onClick={this.onCollapseClick}>
        <div className="tile-trigger">
          <div className="arrow-container">
            <i className={`fa fa-chevron-${isActive ? 'up' : 'down'} expand-icon`}/>
          </div>
        </div>
      </span>
    );

    const error = isActive ? (
      <span className="error-heading">
        <i className="fa fa-exclamation-triangle" />
        { errorMessage }
      </span>
    ) : (
      <div className="error-message">
        <i className="fa fa-exclamation-triangle" />
        <div className="message">{ errorMessage }</div>
      </div>
    );

    return (
      <div className={`project-tile ${isActive ? 'open' : 'closed'}`}>
        <div className="tile-header failed">
          { tileImage }
          { tileTitle }
        </div>

        <div className="tile-body">
          { error }
          { isActive && this.renderDropContent() }
          { tileCollapseBtn }
        </div>
      </div>
    );
  }
});

const BatchTileComponent = React.createClass({
  getInitialState() {
    return {
      documents: null,
      docstats: null,
      isActive: false,
      isLoading: false
    };
  },

  onCollapseClick() {
    const { isActive, documents } = this.state;
    const { uuid, batchId, isOwner, dispatch } = this.props;

    // if open
    if (isActive) return this.setState({ isActive: false });

    // if closed with existing data
    if (documents) {
      return this.setState({ isActive: true })

    // if closed with no data
    } else {
      this.setState({ isLoading: true, isActive: true });
      dispatch(getDocumentDetails(isOwner ? { batchId } : { uuid }))
        .then(res => {
          const { documents, docstats } = res.data;
          this.setState({ isLoading: false, documents, docstats })
        })
        .catch(() => this.setState({ isLoading: false }))
    }
  },

  onTrashClick() {
    const { batchId, openDeleteModal } = this.props;
    const { documents } = this.state;

    openDeleteModal({ batch: true, batch_id: batchId, docs: documents }, this.onCollapseClick);
  },

  renderDropContent() {
    const { isLoading, documents, docstats } = this.state;

    // if loading
    if (isLoading) return <div className="tile-loader"><i className="fa fa-cog fa-spin" /></div>;

    // if error
    if (!documents) return <div className="tile-fetch-error">Error while fetching data</div>;

    const { batchId, defaultRepView } = this.props;
    const { redlines, comments, suggested, keywords } = docstats;

    const docsList = (
      <div className="docs-list">
        { documents.map((doc, key) => {
          return (
            <a key={key} className="docs-name" href={doc.report_url + defaultRepView || ''}>
              <div className="folder-style"/>
              <div className="doc-name-wraper" title={doc.title}>{ doc.title }</div>
            </a>
          );
        }) }
      </div>
    );

    const docsStats = (
      <div className="doc-stats">
        <Stat title="Changes" iconClass="fa fa-clock" value={redlines} />
        <Stat title="Comments" iconClass="fa fa-comment" value={comments} />
        <Stat title="Learners" iconClass="fa fa-lightbulb" value={suggested} />
        <Stat title="Keywords" iconClass="fa fa-bookmark" value={keywords} />
      </div>
    );

    const docsTools = (
      <div className="tile-tools">
        <ExportDocument
          docId={batchId}
          redlines={redlines}
          nrComments={comments}
          isBatch={true}
        />
        <span onClick={this.onTrashClick} className="delete-icon">
          <i className="fa fa-trash"/>
          <div className="delete-text">Delete</div>
        </span>
      </div>
    );

    return (
      <div>
        {docsList}
        {docsStats}
        {docsTools}
      </div>
    )
  },

  render() {
    const { isActive } = this.state;
    const {
      title,
      documentsCount,
      username,
      image,
      created,
      reportUrl
    } = this.props;

    const projectURL = reportUrl;

    const tileImage = (
      <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Owner: {username}</Tooltip>}>
        <img className="owner-avatar" src={image}/>
      </OverlayTrigger>
    );

    const tileTitle = (
      <div className="project-title">
        <div className="project-type batch">
          Batch
        </div>
        <div className="project-name-wrapper batch-title">
          <a className="batch-link" href={projectURL}>{ title }</a>
        </div>
      </div>
    );

    const tileUploaded = !isActive ? null : (
      <div className="date-uploaded-container">
        <Time locale="en"
          value={created} format="MMMM DD, YYYY hh:mm a" />
      </div>
    );

    const tileCollapseBtn = (
      <span onClick={this.onCollapseClick}>
        <div className="tile-trigger">
          <div className="arrow-container">
            <i className={`fa fa-chevron-${isActive ? 'up' : 'down'} expand-icon`}/>
          </div>
        </div>
      </span>
    );

    const docsLength = (
      <div className={`documents-length ${isActive ? 'open' : ''}`}>
        <i className="fa fa-copy" /> {documentsCount} documents
      </div>
    );

    return (
      <div className={`project-tile ${isActive ? 'open' : 'closed'}`}>
        <div className="tile-header">
          { tileImage }
          { tileTitle }
        </div>
        <div className="tile-body">
          { tileUploaded }
          { docsLength }
          { isActive && this.renderDropContent() }
          { tileCollapseBtn }
        </div>
      </div>
    )
  }
});

export const BatchTile = connect()(BatchTileComponent);
