import React from 'react';
import { connect } from 'react-redux';
import Button from 'react-bootstrap/lib/Button';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import ButtonToolbar from 'react-bootstrap/lib/ButtonToolbar';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import uuidV4 from 'uuid/v4';

require('./styles/RevisionControls.scss');


const RevisionControls = React.createClass({

  propTypes: {
    pending: React.PropTypes.bool.isRequired,
    deletePending: React.PropTypes.bool.isRequired,
    unapproved: React.PropTypes.bool.isRequired,
    acceptChange: React.PropTypes.func.isRequired,
    rejectChange: React.PropTypes.func.isRequired,
    submitRevision: React.PropTypes.func.isRequired
  },

  onClickSubmit() {
    this.props.submitRevision();
  },

  render() {
    const { isOwner, isSubmitting } = this.props;
    const hasPendingChanges = this.props.pending;
    const hasPendingDelete = this.props.deletePending;
    const hasUnapprovedChanges = this.props.unapproved;

    const approveTooltip = <Tooltip id={uuidV4()}><strong>Approve Change</strong></Tooltip>;
    const rejectTooltip = <Tooltip id={uuidV4()}><strong>Reject Change</strong></Tooltip>;

    let revisionControls;
    if (isOwner && hasUnapprovedChanges && !hasPendingChanges) {
      revisionControls = (
        <div className="approval-buttons">
          <OverlayTrigger placement="top" overlay={approveTooltip}>
            <i onClick={this.props.acceptChange} className="fa fa-check approve" />
          </OverlayTrigger>
          <OverlayTrigger placement="top" overlay={rejectTooltip}>
            <i onClick={this.props.rejectChange} className="fa fa-times reject" />
          </OverlayTrigger>
        </div>
      );
    } else if (hasPendingChanges) {
      revisionControls = (
        <div className="approval-buttons">
          <ButtonToolbar>
            <Button bsStyle="success" onClick={this.onClickSubmit} disabled={isSubmitting}>
              { isSubmitting ? 'Submitting' : 'Submit' }
            </Button>
          </ButtonToolbar>
        </div>
      );
    } else if (hasPendingDelete) {
      revisionControls = (
        <div className="approval-buttons">
          <ButtonToolbar>
            <Button bsStyle="danger"
              onClick={this.onClickSubmit} disabled={isSubmitting}>
              { isSubmitting ? 'Deleting' : 'Delete' }
            </Button>
          </ButtonToolbar>
        </div>
      );
    }

    return (
      <div className="beagle-revision-controls">
        {revisionControls}
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  return {
    isOwner: (
      state.report.get('uuid') && // Make sure that report has been fetched
      state.report.get('owner').get('username') == state.user.get('username')
    )
  }
};

export default connect(mapStateToProps)(RevisionControls)
