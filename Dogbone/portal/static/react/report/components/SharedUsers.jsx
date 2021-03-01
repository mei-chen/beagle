import _ from 'lodash';

import React from 'react';
import { connect } from 'react-redux';
import $ from 'jquery';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

import log from 'utils/logging';
import userDisplayName from 'utils/userDisplayName';
import SharedUsersModal from 'common/components/SharedUsersModal'
import { Notification } from 'common/redux/modules/transientnotification';
import {
  unInviteUser,
  changeOwner,
  inviteUser
} from 'report/redux/modules/report';

import {
  unInviteUser as unInviteProjectUser,
  changeOwner as changeProjectOwner,
  inviteUser as inviteProjectUser
} from 'account/redux/modules/project';

require('./styles/SharedUsers.scss');
require('utils/styles/confirm.scss')

const SharedUser = React.createClass({

  render() {
    var user = this.props.user;

    let tooltipString = userDisplayName(user);

    var tooltip = <Tooltip id="shared-user-tooltip"><strong>{tooltipString}</strong></Tooltip>;
    var avatarClass = (this.props.extended ? 'shared-avatar' : 'shared-avatar shrinked');

    return (
        <div className="beagle-shared-user">
          <OverlayTrigger placement="bottom" overlay={tooltip}>
            <img className={avatarClass} src={user.avatar} />
          </OverlayTrigger>
        </div>
    );
  }
});

const SharedUsersComponent = React.createClass({
  getDefaultProps() {
    return {
      uuid: null,
      collaborators: [],
      extended: true,
      maxUsers: 6
    };
  },

  getInitialState() {
    return {
      typeaheadOptions: [],
      showCollaboratorsModal: false
    };
  },

  componentDidMount() {
    $.get('/api/v1/user/me/collaborators')
      .done(resp => {
        var emails = _.map(resp.objects, u => u.email);
        this.setState({ typeaheadOptions: emails });
      })
      .fail(resp => log.error(resp));
  },

  /**
  * addUser
  *
  * takes the string in the shared user input element
  * checks for valid email format, if valid call the
  * invite user action, if invalid show the error notification
  * thanks http://stackoverflow.com/a/46181
  */
  addUser(email) {
    const { dispatch, onInvite } = this.props;

    if (email === '') {
      //do nothing (no email to add)
      return;
    }

    if (this.validateEmail(email)) {
      onInvite(email)
    }
    else {
      dispatch(Notification.error(`${email} is an invalid email`));
    }
  },

  /**
  * validateEmail
  *
  * if valid email format return true, else false
  * thanks http://stackoverflow.com/a/46181
  */
  validateEmail(email) {
    var re = /^([\w-\+]+(?:\.[\w-\+]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return re.test(email);
  },

  openModal() {
    this.setState({ showCollaboratorsModal: true })
  },

  closeModal() {
    this.setState({ showCollaboratorsModal: false });
  },

  unInviteUserWraper(collaborator) {
    const { onUninvite } = this.props;
    onUninvite(collaborator);
  },

  changeOwnerWraper(collaborator) {
    const { onChangeOwner } = this.props;
    onChangeOwner(collaborator);
    this.setState({ showCollaboratorsModal: false })
  },

  render() {
    const {
      uuid,
      owner,
      collaborators,
      isOwner: userOwnsDocument,
      extended: extendedSummary,
      maxUsers
    } = this.props;

    const {
      typeaheadOptions,
      showCollaboratorsModal
    } = this.state;

    const displayCollaborators = collaborators.slice(0, maxUsers);
    const collaboratorsWithOwner = [owner].concat(collaborators);

    // generate shared users
    const userClass = extendedSummary ? 'shared-user' : 'shared-user shrinked';
    const displaySharedUsers = (
      displayCollaborators.map((collaborator, index) => {
        return (
          <li className={userClass} key={index}>
            <SharedUser
              user={collaborator}
              uuid={uuid}
              extended={extendedSummary}
            />
          </li>
        )
      })
    );

    // generate users management button
    let usersModalButton;
    const usersModalButtonClass = (extendedSummary ? 'shared-add-user shared-users-modal' : 'shared-add-user shared-users-modal shrinked')
    const usersModalButtonIcon = (
      collaborators.length > maxUsers ?
      <span>+{collaborators.length - maxUsers}</span> :
      <i className="fa fa-ellipsis-v"/>
    );
    if (collaborators.length > 0) {
      usersModalButton = (
        <li className={userClass} key={maxUsers}>
          <OverlayTrigger placement="bottom" overlay={<Tooltip id="collaborators-button-tooltip">Collaborators</Tooltip>}>
            <span className={usersModalButtonClass} onClick={this.openModal}>
              { usersModalButtonIcon }
            </span>
          </OverlayTrigger>
        </li>
      )
    }

    // generate a button to invite shared users if user is owner and no collaborators
    var addSharedUserButton;
    const addSharedUserButtonClass = (extendedSummary ? 'shared-add-user' : 'shared-add-user shrinked')
    if (userOwnsDocument && collaborators.length === 0) {
      addSharedUserButton = (
        <li className={userClass}>
          <OverlayTrigger placement="bottom" overlay={<Tooltip id="invite-button-tooltip">Invite User</Tooltip>}>
            <span onClick={this.openModal} className={addSharedUserButtonClass}>
              <i className="fa fa-user-plus"/>
            </span>
          </OverlayTrigger>
        </li>
      );
    }

    const usersContainerClass = (
      extendedSummary ? 'shared-users-container' : 'shared-users-container shrinked-container'
    );

    return (
      <div className={usersContainerClass}>
        <div className="shared-users-wrap">
          <ul className="shared-users">
            {displaySharedUsers}
            {usersModalButton}
            {addSharedUserButton}
          </ul>
        </div>
        <SharedUsersModal
          uuid={uuid}
          inviteUser={this.addUser}
          unInviteUser={this.unInviteUserWraper}
          changeOwner={this.changeOwnerWraper}
          show={showCollaboratorsModal}
          onHide={this.closeModal}
          collaborators={collaboratorsWithOwner}
          isOwner={userOwnsDocument}
          typeaheadOptions={typeaheadOptions}
          onOwnerChange={this.closeModal}
        />
      </div>
    );
  },
});


const mapStateToProps = (state) => {
  return {
    isOwner: (
      state.report.get('uuid') && // Make sure that report has been fetched
      state.report.get('owner').get('username') == state.user.get('username')
    )
  }
};

const mapDistpatchToProps = (dispatch) => {
  return {
    onInvite(email) {
      dispatch(inviteUser(email))
    },
    onUninvite(user) {
      dispatch(unInviteUser(user))
    },
    onChangeOwner(user) {
      dispatch(changeOwner(user))
    }
  }
};

const mapStateToPropsProject = () => ({});

const mapDistpatchToPropsProject = (dispatch, ownProps) => {
  const { uuid } = ownProps;

  return {
    onInvite(email) {
      dispatch(inviteProjectUser(uuid, email))
    },
    onUninvite(user) {
      dispatch(unInviteProjectUser(uuid, user.email))
    },
    onChangeOwner(user) {
      dispatch(changeProjectOwner(uuid, user.email))
    }
  }
};

// PROJECT TILE MODE
export const SharedUsersProject = connect(mapStateToPropsProject, mapDistpatchToPropsProject)(SharedUsersComponent)

// DEFAULT (REPORT) MODE
export default connect(mapStateToProps, mapDistpatchToProps)(SharedUsersComponent)
