import React, { Component, PropTypes } from 'react';
import { Button, Popover, OverlayTrigger } from 'react-bootstrap';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import Shared from './Shared';

import {
  create as createPermalink,
  removeFromServer,
  editOnServer
} from 'permalink/redux/modules/permalink';

class ReportShared extends Component {
   constructor(props) {
        super(props);
        this.state = {};
    }

    _renderSharedLinks() {
        const { report, permalink, removeFromServer, editOnServer, onPermalinkChange } = this.props;

        return report.get("report_shared").map(link => (
            <Shared 
                key={link.get('id')}
                link={link}
                onRemoveClick={(id) => removeFromServer(id).then(onPermalinkChange)}
                onEdit={(id, name) => editOnServer(id, name).then(onPermalinkChange)} />
        ))
    }

    render() {
        const { report, createPermalink, onPermalinkChange } = this.props;
        const popoverTitle = (
            <strong>Publicly available</strong>
        );
        const infoPopover = (
            <Popover id="popover-trigger-hover-focus" title={popoverTitle}>
                Use names to manage them. To restrict access, remove the specific links.
            </Popover>
        );
        return (
            <div className='sharable-links'>
                <div className='sharable-links-header'>
                    <span className="sharable-links-title">
                        Sharable URLs
                    </span>
                    <OverlayTrigger trigger={['hover', 'focus']} placement="bottom" overlay={infoPopover}>
                        <i className="fa fa-info-circle" aria-hidden="true"></i>
                    </OverlayTrigger>
                    <Button
                        className="sharable-links-button"
                        bsStyle="info"
                        bsSize="xs"
                        onClick={() => createPermalink({ report: report.get('id') }).then(onPermalinkChange)}>
                        <i className="fa fa-plus" /> Generate New URL
                    </Button>
                </div>

                <div className='sharable-links-body'>
                    { this._renderSharedLinks() }
                </div>
            </div>
        )
    }
}

const mapStateToProps = (state) => {
  return {
    permalink: state.permalink
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    createPermalink,
    removeFromServer,
    editOnServer
  }, dispatch)
};

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ReportShared);