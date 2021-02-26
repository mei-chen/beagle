import React from 'react';
import { connect } from 'react-redux';
import Modal from 'react-bootstrap/lib/Modal';
import uuidV4 from 'uuid/v4';
import Timestamp from 'react-time';
import CriticalActionButton from 'common/components/CriticalActionButton';
import Button from 'react-bootstrap/lib/Button';
import { Typeahead } from 'react-typeahead';

import { getFromServer as getViewedByFromServer } from 'common/redux/modules/viewed_by'

import 'common/components/styles/SharedUsersModal.scss'

const SharedUserModalComponent = React.createClass({

  getDefaultProps() {
    return {
      isOwner: false,
      canChange: false,
      canDelete: false
    };
  },

  changeOwner() {
    const { collaborator, changeOwner } = this.props;

    changeOwner(collaborator);
  },

  deleteUser() {
    const { collaborator, unInviteUser } = this.props;

    unInviteUser(collaborator);
  },

  render() {
    const collaborator = this.props.collaborator;
    const unInviteTitle = (
      <span>
        <i className="fa fa-times" aria-hidden="true"/>&nbsp;
        Un-invite
      </span>
    )
    const changeOwnerTitle = (
      <span>
        <i className="fa fa-key" aria-hidden="true"/>&nbsp;
        Make owner
      </span>
    )
    const lastViewed = (
      <span>
        { this.props.isInitialized ?
          (this.props.lastAccess ?
            (<span>
              <i className="fa fa-check-square" aria-hidden="true"/>&nbsp;last viewed&nbsp;
              <Timestamp
                value={this.props.lastAccess}
                locale="en"
                titleFormat="YYYY/MM/DD HH:mm"
                relative
              />
            </span>) :
            (<span>
              <i className="fa fa-square" aria-hidden="true"/>&nbsp;Not viewed yet
            </span>)) :
          (<span>
            <i className="fa fa-spinner fa-spin fa-3x fa-fw" aria-hidden="true"/>
          </span>)
        }
      </span>
    )
    const criticalActions = (
      <span>
        <div className="action">
          <CriticalActionButton
            title={unInviteTitle}
            mode="active"
            action={this.deleteUser}/>
        </div>
        <div className="action owner">
          <CriticalActionButton
            styleClass="ch-onwer-class"
            title={changeOwnerTitle}
            mode="active"
            action={this.changeOwner}/>
        </div>
      </span>
    )

    return (
      <div className={this.props.isOwnerUser ? 'modal-user owner' : 'modal-user'}>
        <div className="modal-avatar-wraper">
          <img className="modal-avatar" src={collaborator.avatar}/>
        </div>
        <div className="info-wraper">
          <div className="name" title={collaborator.first_name + ' ' + collaborator.last_name}>
            {collaborator.first_name} {collaborator.last_name}
          </div>
          <div className="name smaller" title={collaborator.email}>
            {collaborator.email}
          </div>
          <div className="login">
            {lastViewed}
          </div>
        </div>
        {this.props.isOwner && !this.props.isOwnerUser && criticalActions }
      </div>
    );
  }
});

const SharedUserModal = connect()(SharedUserModalComponent)

const SharedUsersModal = React.createClass({

  componentDidMount() {
    // Get the data from the api here.
    const { dispatch, uuid } = this.props;
    dispatch(getViewedByFromServer(uuid));
  },

  inviteUserWrapper(email) {
    this.props.inviteUser(email)
    this.refs.invite.setEntryText('');
  },

  render() {
    const { collaborators,
            isOwner,
            show,
            onHide,
            changeOwner,
            unInviteUser,
            documentName,
            viewed_by,
            typeaheadOptions
          } = this.props;

    const { viewed_by_users,
            isInitialized
          } = viewed_by

    const modalUsers = (
      collaborators.map((collaborator, i) => {
        const isOwnerUser = i === 0;
        return (
          <SharedUserModal
            lastAccess={viewed_by_users[collaborator.username]}
            isInitialized={isInitialized}
            key={uuidV4()}
            collaborator={collaborator}
            isOwner={isOwner}
            isOwnerUser={isOwnerUser}
            changeOwner={changeOwner}
            unInviteUser={unInviteUser}
          />
        )
      })
    );

    //show the user searchbar or leave it
    let modalSearchBar;
    if (isOwner) {
      modalSearchBar = (
        <div className="user-search-wrap">
          <div className="user-search">
            <Typeahead
              ref="invite"
              maxVisible={5}
              placeholder="Search email of existing user"
              options={typeaheadOptions}
              onOptionSelected={email => this.inviteUserWrapper(email)}
            />
          </div>
          <Button ref="submitInviteButton" className="add-btn" onClick={() => this.inviteUserWrapper(this.refs.invite.state.entryValue)}>
            <i className="fa fa-plus" aria-hidden="true"/>&nbsp;Add
          </Button>
        </div>
      )
    }


    const documentTitle = (
      <div className="modal-doc-title" title={documentName}>
        {documentName}
      </div>
    );

    return (
      <Modal show={show} onHide={onHide} aria-labelledby="contained-modal-title-sm">
        <Modal.Header className="my-modal-header">
          <Modal.Title id="contained-modal-title-sm">Collaborators</Modal.Title>
          {documentTitle}
        </Modal.Header>
        <Modal.Body className="my-modal-body">
          <div className="modal-collaborators-list">
            {modalUsers}
          </div>
          {modalSearchBar}
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={this.props.onHide}>Close</Button>
        </Modal.Footer>
      </Modal>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    viewed_by: state.viewed_by.toJS(),
  }
};

export default connect(mapStateToProps)(SharedUsersModal)
