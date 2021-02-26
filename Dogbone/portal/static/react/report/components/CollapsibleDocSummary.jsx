import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import Time from 'react-time'
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import uuidV4 from 'uuid/v4';
import SharedUsers from './SharedUsers';
import InplaceEditForm from './InplaceEditForm'
import ExportDocument from './ExportDocument'
import userDisplayName from 'utils/userDisplayName';
import $ from 'jquery';

require('./styles/CollapsibleDocSummary.scss');

const ShrinkedSummary = React.createClass({

  onBackToTopClick() {
    $('html, body').animate({
      // back to the top son
      scrollTop: 0
    });
  },

  render() {
    const { report } = this.props;
    const documentName = report.get('title');
    const avatar = report.get('owner').get('avatar');
    const documentType = report.get('agreement_type') || 'Agreement';
    const parties = report.get('analysis').get('parties').toJS();
    const ownerTooltip = (
      <Tooltip id={uuidV4()}>
        {userDisplayName(report.get('owner').toJS())}
      </Tooltip>
    );

    return (
      <span className="summary-contetn-wraper">
        <OverlayTrigger placement="bottom" overlay={ownerTooltip}>
          <img src={avatar} className="avatar shrinked"/>
        </OverlayTrigger>
        <div className="stats">
          <span id="doctype-shrinked">{documentType}</span>
          <div title={documentName} className="shrinked-summary-title">
            {documentName}
          </div>
        </div>
        <div className="stats shrinked-party-wrapper">
          <InplaceEditForm parties={parties} shrinked={true}/>
        </div>
        <div className="stats top-button-wrapper" onClick={this.onBackToTopClick}>
          <div className="to-top-arrow"><i className="fa fa-long-arrow-up"/></div>
          <span className="to-top-text"> to top </span>
        </div>
        <div className="stats separator"/>
        <div className="stats shrinked-export-wrapper">
          <div className="export-wrapper">
            <ExportDocument/>
          </div>
        </div>
        <div className="stats separator"/>
        <div className="stats shrinked-shared-users-wrapper">
          <SharedUsers
            uuid={report.get('uuid')}
            collaborators={report.get('collaborators').toJS()}
            owner={report.get('owner').toJS()}
            extended={false}
          />
        </div>
      </span>
    )
  }
})

const ExtendedSummary = React.createClass({
  render() {
    const { report } = this.props;
    const documentName = report.get('title');
    const parties = report.get('analysis').get('parties').toJS();
    const avatar = report.get('owner').get('avatar');
    const documentTypeConfidence = Math.round(report.get('agreement_type_confidence') * 100);
    const documentType = report.get('agreement_type') || 'Agreement';
    const article = documentType[0] == 'A' ? 'an' : 'a';
    const doctypeTooltip = (
      <Tooltip id={uuidV4()}>{documentTypeConfidence}% confidence</Tooltip>
    );
    const uploadedTime = (
      <Time
        value={report.get('created')}
        locale="en"
        format="MMMM DD, YYYY hh:mm a" />
    );
    const ownerTooltip = (
      <Tooltip id={uuidV4()}>
        {userDisplayName(report.get('owner').toJS())}
      </Tooltip>
    );

    return (
      <span className="summary-contetn-wraper extended">
        <OverlayTrigger placement="bottom" overlay={ownerTooltip}>
          <img src={avatar} className="avatar"/>
        </OverlayTrigger>
        <div className="stats">
          <div title={documentName} className="summary-title">
            {documentName}
          </div>
          <div className="parties" id={this.props.show && 'step2'}>
            This is {article}
            <OverlayTrigger placement="bottom" overlay={doctypeTooltip}>
              <span id="doctype">{documentType}</span>
            </OverlayTrigger>
            <InplaceEditForm parties={parties}/>
          </div>
        </div>
        <ExportDocument extended/>
        <div className="calendar-icon">
          <OverlayTrigger placement="left" overlay={<Tooltip id={uuidV4()}>Uploaded on {uploadedTime}</Tooltip>}>
            <i className="fa fa-calendar-alt" aria-hidden="true"/>
          </OverlayTrigger>
        </div>
        <SharedUsers
          uuid={report.get('uuid')}
          collaborators={report.get('collaborators').toJS()}
          owner={report.get('owner').toJS()}
        />
      </span>
    )
  }
})


const CollapsibleDocSummary = React.createClass({

  getInitialState() {
    return {
      showExtended: true
    }
  },

  componentDidMount() {
    this.initializeUpdateViewPort();
  },

  componentWillUnmount() {
    if (this._updateViewportListener) {
      window.removeEventListener('scroll', this._updateViewportListener);
    }
  },

  // Causing display bugs
  initializeUpdateViewPort() {
    this._updateViewportListener = _.throttle(this.updateViewport, 100);
    window.addEventListener('scroll', this._updateViewportListener);
    this.updateViewport();
  },

  updateViewport() {
    let newState = {
      showExtended: !(window.pageYOffset > 60)
    };
    this.setState(newState);
  },

  render() {
    const { report } = this.props;
    const extended = (
      <ExtendedSummary
        report={report}
        show={this.state.showExtended}
      />
    );
    const shrinked = (
      <ShrinkedSummary
        report={report}
        show={!this.state.showExtended}
      />
    );

    return (
      <span>
        <div className={'collapsible-summary' + (this.state.showExtended ? ' extended' : ' hiden')}>
          {extended}
        </div>
        <div className={'collapsible-summary' + (!this.state.showExtended ? '' : ' hiden extended')}>
          {shrinked}
        </div>
      </span>
    )
  }
})

const mapStateToProps = (state) => {
  return {
    report: state.report,
    isInitialized: state.report.get('isInitialized')
  }
};

export default connect(mapStateToProps)(CollapsibleDocSummary)