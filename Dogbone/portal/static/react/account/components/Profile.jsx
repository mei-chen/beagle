/* React Library Includes */
import React from 'react';
import { connect } from 'react-redux';
import Button from 'react-bootstrap/lib/Button';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import SideMenuButton from 'common/components/SideMenuButton';

require('./styles/Profile.scss');   //stylings for component


const Profile = React.createClass({

  getInitialState() {
    return {
      viewMode: 'project',
    };
  },

  render() {
    const user = this.props.user;
    const company = user.get('company') ? 'at ' + user.get('company') : '';

    const projectActive = this.props.viewMode == 'project';
    const learnersActive = this.props.viewMode == 'learners';
    const keywordsActive = this.props.viewMode == 'keywords';
    const SettingsActive = this.props.viewMode == 'settings';
    return (
      <div className="profile-column">
        <a href="/account#/edit-account">
          <OverlayTrigger placement="bottom" overlay={<Tooltip id="tooltip-top"><strong>Edit Profile Picture</strong></Tooltip>}>
            <img onClick={this.handleEdit} className="profile-avatar" src={user.get('avatar')} />
          </OverlayTrigger>
        </a>
        <div className="profile-name">
          {user.get('first_name')} {user.get('last_name')}
        </div>
        <span className="profile-title">{user.get('job_title')}</span>
        <span className="profile-company-name">{company}</span>
        <span className="profile-email">
          <i className="fa fa-envelope"/>
          <span>{user.get('email')}</span>
        </span>
        <a href="/account#/edit-account">
          <div className="edit-account-button">
            <Button>
              <i className="fa fa-pencil" /> Edit Profile
            </Button>
          </div>
        </a>
        <div className="hrseparator" />
        <a href="account#/projects" className="no-underline">
          <div className="project-button">
            <SideMenuButton active={projectActive}>
              <i className="fa fa-th fa-fw" /> Your Documents
            </SideMenuButton>
          </div>
        </a>
        <a href="/account#/manage-learners" className="no-underline">
          <div className="learners-dashboard-button">
            <SideMenuButton active={learnersActive}>
              <i className="fa fa-lightbulb fa-fw" /> Manage Learners
            </SideMenuButton>
          </div>
        </a>
        <a href="/account#/manage-keywords" className="no-underline">
          <div className="keywords-dashboard-button">
            <SideMenuButton active={keywordsActive}>
              <i className="fa fa-bookmark fa-fw" /> Manage Keywords
            </SideMenuButton>
          </div>
        </a>
        <a href="/account#/settings" className="no-underline">
          <div className="keywords-dashboard-button">
            <SideMenuButton active={SettingsActive}>
              <i className="fa fa-cog fa-fw" /> Account Settings
            </SideMenuButton>
          </div>
        </a>
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    user: state.user
  }
};

export default connect(mapStateToProps)(Profile)
