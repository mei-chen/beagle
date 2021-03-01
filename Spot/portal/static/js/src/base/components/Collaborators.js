import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List } from 'immutable';
import { OverlayTrigger, Tooltip, Modal, ModalHeader, ModalBody, ModalFooter, Button, FormControl, Form, Alert, Pagination, Popover } from 'react-bootstrap';
import Timestamp from 'react-time';

import { getFromServer, inviteOnServer, uninviteOnServer, EXPERIMENT, DATASET } from 'base/redux/modules/collaborators_module';

class Collaborators extends Component {
  constructor(props) {
    super(props);
    this._handleSubmit = this._handleSubmit.bind(this);
    this._handleChange = this._handleChange.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._showModal = this._showModal.bind(this);
    this._renderCollaborators = this._renderCollaborators.bind(this);
    this._renderErrorMessages = this._renderErrorMessages.bind(this);
    this._renderPendingInvites = this._renderPendingInvites.bind(this);
    this._handlePaginationClick = this._handlePaginationClick.bind(this);
    this._handleUninviteClick = this._handleUninviteClick.bind(this);
    this.SHOW_AMOUNT = 5;
    this.state = {
      showModal: false,
      email: '',
      pageNum: 1
    }
  }

  componentWillMount() {
    const { getFromServer, entity, id, isOwner } = this.props;
    isOwner && getFromServer(entity, id);
  }

  _handleChange(e) {
    this.setState({ email: e.target.value });
  }

  _handleSubmit(e) {
    e.preventDefault();

    const { inviteOnServer, entity, id } = this.props;
    const { email } = this.state;
    inviteOnServer(entity, id, email).then(_ => this.setState({ email: '' }));
  }

  _handlePaginationClick(pageNum) {
    this.setState({ pageNum })
  }

  _handleUninviteClick(username) {
    const { entity, id, uninviteOnServer, getFromServer } = this.props;
    uninviteOnServer(entity, id, username).then(_ => getFromServer(entity, id));
  }

  _showModal() {
    this.setState({ showModal: true });
  }

  _hideModal() {
    this.setState({ showModal: false });
  }

  _renderCollaborators(collaborators) {
    return collaborators.map((collab, i) => (
      <div
        key={i}
        className="collab clearfix">
        <div className="collab-avatar">
          { collab.get('image') ? <img className="collab-image" src={collab.get('image')} /> : <i className="collab-placeholder fa fa-user" /> }
        </div>
        <div className="collab-controls">
          <span
            className="collab-control"
            onClick={() => { this._handleUninviteClick( collab.get('username') ) }}>Un-invite</span>
        </div>
        <div className="collab-info">
          { collab.get('full_name') && (
            <span className="collab-name">{ collab.get('full_name') }</span>
          ) }
          <span className="collab-email">{ collab.get('email') }</span>
            { collab.get('last_login') && (
              <span className="collab-last-seen">
                Last login <Timestamp
                value={ collab.get('last_login') }
                locale="en"
                titleFormat="YYYY/MM/DD HH:mm"
                relative />
              </span>
            ) }
        </div>
      </div>
    ));
  }

  _renderErrorMessages(errors) {
    return errors.map((err, i) => <Alert key={i} bsStyle="danger">{err}</Alert>);
  }

  _renderPendingInvites(pendingInvites) {
    const popover = (
      <Popover id="popover-pending-invites" title="Pending invites">
        { pendingInvites.map((email, i) => <div key={i} className="collaborators-pending-invite">{ email }</div>) }
      </Popover>
    );

    return (
      <OverlayTrigger placement="left" overlay={popover}>
        <span>Pending invites: <strong>{ pendingInvites.size }</strong></span>
      </OverlayTrigger>
    )
  }

  render() {
    const { isOwner, ownerUsername, collaborators, pendingInvites, inviteErrorMessages } = this.props;
    const { showModal, email, pageNum } = this.state;
    const tooltip = <Tooltip id="tooltip">{ isOwner ? 'Collaborators' : 'In collaboration'}</Tooltip>
    const popover = <Popover id="popover" title={`Owned by ${ownerUsername}`}>You are a collaborator</Popover>

    if(!isOwner) {
      return (
        <div className="collaborators-wrap">
          <OverlayTrigger placement="bottom" overlay={popover}>
            <i className="collaborators-not-owner fa fa-portrait" />
          </OverlayTrigger>
        </div>
      )
    }

    return(
      <div className="collaborators">
        {/* toggle */}
        <OverlayTrigger placement="bottom" overlay={tooltip}>
          <div className="collaborators-wrap">
            <span
              className="collaborators-toggle"
              onClick={this._showModal}>
              <i className="collaborators-icon fa fa-users" />
              { collaborators.size > 0 && <span className="collaborators-amount">{ collaborators.size }</span> }
            </span>
          </div>
        </OverlayTrigger>

        {/* modal */}
        <Modal
          show={showModal}
          onHide={this._hideModal}
          className="collaborators-modal">

          <ModalHeader closeButton>
            <strong>Collaborators</strong>
          </ModalHeader>

          <ModalBody className="collaborators-modal-body">
            { collaborators.size > 0 && (
              <div>
                <div className="collaborators-list">
                  { this._renderCollaborators(collaborators.slice((pageNum - 1) * this.SHOW_AMOUNT, (pageNum - 1) * this.SHOW_AMOUNT + this.SHOW_AMOUNT)) }
                </div>

                { collaborators.size > this.SHOW_AMOUNT && (
                  <div className="collaborators-pagination">
                    <Pagination
                      prev
                      next
                      ellipsis
                      boundaryLinks
                      items={Math.ceil(collaborators.size / this.SHOW_AMOUNT)}
                      maxButtons={5}
                      activePage={pageNum}
                      onSelect={this._handlePaginationClick} />
                  </div>
                ) }
              </div>
            ) }

            { pendingInvites.size > 0 && (
              <div className="collaborators-pending">
                { this._renderPendingInvites(pendingInvites) }
              </div>
            )}
          </ModalBody>

          <ModalFooter>
            <Form
              className="collaborators-form"
              onSubmit={this._handleSubmit}>
              { inviteErrorMessages.size > 0 && this._renderErrorMessages(inviteErrorMessages) }
              <Button
                type="submit"
                className="collaborators-button"
                bsStyle="primary">Invite</Button>

              <div className="collaborators-input-wrap">
                <FormControl
                  type="text"
                  placeholder="Email"
                  value={email}
                  onChange={this._handleChange}
                />
              </div>
            </Form>
          </ModalFooter>
        </Modal>
      </div>
    )
  }
}

Collaborators.propTyepes = {
  isOwner: PropTypes.bool.isRequired,
  ownerUsername: PropTypes.string.isRequired,
  entity: PropTypes.oneOf([EXPERIMENT, DATASET]),
  id: PropTypes.number.isRequired,
  collaborators: PropTypes.instanceOf(List).isRequired,
  pendingInvites: PropTypes.instanceOf(List).isRequired,
  inviteErrorMessages: PropTypes.instanceOf(List).isRequired
}


const mapStateToProps = (state) => {
  return {
    collaborators: state.collaboratorsModule.get('collaborators'),
    pendingInvites: state.collaboratorsModule.get('pendingInvites'),
    inviteErrorMessages: state.collaboratorsModule.get('inviteErrorMessages')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    inviteOnServer,
    uninviteOnServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(Collaborators);
