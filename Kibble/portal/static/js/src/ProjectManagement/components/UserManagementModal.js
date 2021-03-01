import React from "react";
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Button, Input } from 'react-bootstrap';
import {
  getCollaboratorsForProject,
  requestCollaborators,
  inviteCollaborator,
  unInviteCollaborator
} from "ProjectManagement/redux/actions";
import { Spinner } from 'base/components/misc.js'
import { MODULE_NAME } from "ProjectManagement/constants";

import 'react-select/dist/react-select.css';
import 'ProjectManagement/scss/collaborators.scss';

class Collaborators extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      input_user: ''
    };

    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleInviteUser = this.handleInviteUser.bind(this);
    this.handleUnInviteUser = this.handleUnInviteUser.bind(this);
  }

  handleInputChange(e) {
    this.setState({
      input_user:e.target.value
    })
  }

  handleInviteUser() {
    const { getCollaborators, inviteUser, id } = this.props;
    const { input_user } = this.state;
    input_user !== '' && inviteUser(id,{email: input_user});
    this.userInput.value = '';
  }

  handleUnInviteUser (user) {
    const { getCollaborators, unInviteUser, id } = this.props;
    unInviteUser(id,{username:user});
  }

  render() {
    const { collaborators } = this.props;
    return(
      <div className="collaborators">
        <div className="collaborators-wrapper">
        { collaborators.map((item,key) => {
          return (
            <div key={key} className="collaborator">
              {item.username}
              <span onClick={() => this.handleUnInviteUser(item.username)}>
                <i className="fal fa-times"></i>
              </span>
            </div>
          )
        })}
        </div>
        <div className="collaborators-tools">
          <input
            className="input-user"
            ref={(input) => { this.userInput = input; }}
            onChange={this.handleInputChange}
            placeholder="Search email of existing user..."
          />
          <Button onClick={this.handleInviteUser}>
            <i className="fal fa-plus"></i>
            Add
          </Button>
        </div>
      </div>
    )
  }
}

class UserManagementModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
    };
  }

  componentDidMount() {
    const { getCollaboratorsForProject, requestCollaborators, id } = this.props;
    requestCollaborators();
    getCollaboratorsForProject(id);
  }

  render() {
    const {
      id,
      collaborators_ready,
      collaborators_error,
      inviteCollaborator,
      unInviteCollaborator,
      collaborators
    } = this.props;
    return (
      <div>
        {collaborators_ready ?
          (
            collaborators_error ?
              <div className="fail-message-wrapper">
                <i className="fa fa-exclamation-triangle"></i>
                Error getting collaborators
              </div> :
              <Collaborators
                collaborators={collaborators}
                inviteUser={inviteCollaborator}
                unInviteUser={unInviteCollaborator}
                getCollaborators={getCollaboratorsForProject}
                id={id}
              />
          ) :
          <Spinner/>
        }
      </div>
    )
  }
}

const mapStateToProps = (state) => {
  return {
    collaborators_ready: state[ MODULE_NAME ].get('collaborators_ready'),
    collaborators_error: state[ MODULE_NAME ].get('collaborators_error'),
    collaborators: state[ MODULE_NAME ].get('collaborators')
  };
};

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({
    getCollaboratorsForProject,
    requestCollaborators,
    inviteCollaborator,
    unInviteCollaborator
  }, dispatch)
};

export default connect(mapStateToProps,mapDispatchToProps)(UserManagementModal);