import React from 'react';
import { connect } from 'react-redux';
import classNames from 'classnames';
import Crouton from 'react-crouton';
import OnClickOutside from 'react-onclickoutside';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import TransientNotificationsContainer from './TransientNotifications';

import localStore from 'utils/localStore';

import PersistentNotifications from './PersistentNotifications';
import { isLoggedIn } from 'utils/auth';

require('./styles/Header.scss');   //stylings for component

const INTERCOM_ACTIVATOR = 'beagle-intercom';
const DISMISS_CROUTON = 'didDismissCrouton';

if (__ENV__ === 'local') {
  window.$ = require('jquery');
}

const UserActionsDropdown = OnClickOutside(React.createClass({
  propTypes: {
    hideMe: React.PropTypes.func.isRequired,
    isActive: React.PropTypes.bool.isRequired,
    highlightManuals: React.PropTypes.bool.isRequired
  },

  componentDidUpdate(oldProps) {
    if (oldProps.isActive !== this.props.isActive) {
      Intercom('reattach_activator');
    }
  },

  handleClickOutside() {
    this.props.hideMe();
  },

  render() {
    if (!this.props.isActive) {
      // wrapping the activator in an outer div
      // if the id is attached to this top level div, Intercom associated the
      // entire dropdown as the activator. Any link in the dropdown opened the
      // Intercom window.
      return <div><div id={INTERCOM_ACTIVATOR}/></div>;
    }

    //apply highlighting to 'Manuals'
    var highlightStyle;
    if (this.props.highlightManuals) {
      highlightStyle = { 'font-weight': 'bold' }
    }

    return (
      <div className="header-dropdown user-actions-dropdown ignore-react-onclickoutside">
        <div className="dropdown-arrow" />
        <a href="/account#/projects" onClick={this.props.hideMe}>
          <i className="fa fa-th" /> Your Documents
        </a>
        <a href="/account#/settings" onClick={this.props.hideMe}>
          <i className="fa fa-cog" /> Account Settings
        </a>
        <div className="separator"/>
        <a id={INTERCOM_ACTIVATOR} onClick={() => {
          window.Intercom('show');
          this.props.hideMe();
        }}>
          <i className="fa fa-question" /> Chat With Us
        </a>

        <OverlayTrigger
          placement="left"
          overlay={<Tooltip id="tooltip-left">
            Coming soon
          </Tooltip>}>
          <span href="http://docs.beagle.ai" target="_blank" style={highlightStyle}>
            <i className="fa fa-medkit" /> Manuals
          </span>
        </OverlayTrigger>

        <div className="separator"/>
        <a href="/redeem-coupon">
          <i className="fa fa-ticket" /> Redeem Coupon
        </a>
        <a href="/purchase">
          <i className="fa fa-credit-card" /> Purchase
        </a>
        <div className="separator"/>
        <a href="/logout">
          <i className="fa fa-sign-out" /> Sign out
        </a>
      </div>
    );
  }
}));


const Header = React.createClass({
  propTypes: {
    shouldShrink: React.PropTypes.bool.isRequired,
  },

  getDefaultProps() {
    return {
      shouldShrink: false
    };
  },

  getInitialState() {
    return {
      activeUserActionsDropdown: false,
      showCrouton: true,
      wizardDropDownLock: false,
    }
  },

  userActionsDropdown(callback) {
    if (!!callback && typeof callback === 'function') {
      this.setState({
        activeUserActionsDropdown: !this.state.activeUserActionsDropdown
      }, callback);
    //no callback provided
    } else {
      this.setState({ activeUserActionsDropdown: !this.state.activeUserActionsDropdown });
    }
  },

  hideUserActionsDropdown() {
    //don't let this dropdown get closed when the wizard is running
    if (!this.state.wizardDropDownLock) {
      this.setState({
        activeUserActionsDropdown: false
      });
    }
  },

  onDismissCrouton() {
    document.body.classList.remove('crouton-shown');
    this.setState({ showCrouton : false });
    localStore.set(DISMISS_CROUTON, true, 1);
    // the last 1 indicates the cookie expires after 1 day
    // note that if localStorage is available, there is no expiry
  },

  generateCrouton() {
    let isChrome = (window.browser && window.browser.chrome) || window.navigator.userAgent.match('CriOS') || false;
    let didAlreadyDismiss = !!localStore.get(DISMISS_CROUTON);
    let crouton;

    if (!isChrome && !didAlreadyDismiss) {
      document.body.classList.add('crouton-shown');

      var croutonData = {
        id: Date.now(),
        type: 'error',
        message: "Looks like you're using an unsupported browser. We prefer Chrome, however feel free to continue and let us know how it goes!",
        autoMiss: true || false,
        onDismiss: this.onDismissCrouton,
        buttons: [{
          name: '×',
        }],
        hidden: false,
        timeout: 2000
      }
      crouton = <Crouton {...croutonData} />;
    }
    return crouton
  },

  handleSubscription() {
    window.location = '/purchase';
  },

  goToGetStarted() {
    window.location = '/getstarted';
  },

  render() {
    //if unsupported browser
    let crouton, navBar, displayName = '';
    const { user } = this.props;

    if (this.state.showCrouton) {
      crouton = this.generateCrouton();
    }

    let headerClasses = classNames(
      'beagle-header',
      this.props.shouldShrink ? 'shrinkable' : null,
    );

    let navBarClasses = classNames(
      'header-right-nav',
    );

    // if request for user info was made (no matter successful or not)
    if (user.get('isInitialized')) {
      if (!user.get('username')) {
        // no session active display sign in button
        navBar = (
          <ul className={navBarClasses}>
            <li className="header-nav-item">
              <a href="/login" className="header-nav-sign-in">
                Sign In
              </a>
            </li>
          </ul>
        );
      } else {
        // Display signed in user name + logout button
        var avatar = user.get('avatar');
        var username = user.get('username');
        var firstName = user.get('first_name') || '';
        var lastName = user.get('last_name') || '';
        var fullName = (firstName + ' ' + lastName).trim();
        displayName = fullName !== '' ? fullName : username;

        var uploadDocPlusSign;
        if (user.get('is_paid')) {
          uploadDocPlusSign = (
            <li className="header-nav-item nav-upload">
                <a href="/upload/file" className="header-nav-item-link">
                  <i className="header-nav-item-icon fa fa-plus" /> Upload
                </a>
            </li>
          );
        }

        var additionalHeaderMessage;
        //Pre-existing users have no current subscription object be careful
        const {
          subscription
        } = this.props;
        if (subscription.get('current_subscription')) {
          const currentSubscription = subscription.get('current_subscription');
          const isTrial = currentSubscription.get('is_trial');
          if (isTrial) {
            const daysRemaining = currentSubscription.get('display_days_remaining');
            let message;
            if (daysRemaining > 1) {
              message = <span><strong>{daysRemaining}</strong> trial days remaining</span>;
            } else if (daysRemaining === 1) {
              message = <span><strong>final</strong> trial day</span>;
            } else {
              message = <span>trial has expired.</span>;
            }
            additionalHeaderMessage = (
              <li className="header-nav-item">
                <span onClick={this.handleSubscription} className="header-nav-item-link trial-link">{message}</span>
              </li>
            );
          }
        } else if (!user.get('is_paid')) {
          additionalHeaderMessage = (
            <li className="header-nav-item">
              <span onClick={this.goToGetStarted} className="header-nav-item-link trial-link">
                <strong>Get started</strong>
              </span>
            </li>
          );
        }

        var notifications;
        if (isLoggedIn()) {
          notifications = (
            <li className="header-nav-item">
              <PersistentNotifications />
            </li>
          );
        }

        let avatarStyles = {
          backgroundImage: avatar ? `url('${avatar}')` : null
        }

        let dropdownButtonClasses = classNames(
          'header-nav-item-link',
          'link-user-actions-dropdown',
          'ignore-react-onclickoutside'
        );

        navBar = (
          <ul id="step4" className={navBarClasses}>
              {additionalHeaderMessage}
              {uploadDocPlusSign}
              {notifications}
              <li className="header-nav-item">
                <a href="/account#/projects" className="header-nav-item-link account-link">
                  <div style={avatarStyles} className="avatar" />
                  <div className="user-name">
                    {displayName}
                  </div>
                </a>
              </li>
              <li className="header-nav-item">
                <div onClick={this.userActionsDropdown} className={dropdownButtonClasses}>
                  <i className="header-nav-item-icon fa fa-angle-down" />
                </div>
                <UserActionsDropdown
                  hideMe={this.hideUserActionsDropdown}
                  isActive={this.state.activeUserActionsDropdown}
                  highlightManuals={this.state.wizardDropDownLock}
                />
              </li>
          </ul>
        );
      }
    }

    let logoClasses = classNames(
      'header-logo',
    );

    return (
      <div>
        <div id="header" className={headerClasses}>
          {crouton}
          <div className="header-wrap">
            <div className={logoClasses}>
              <a href="/upload/file" title="Beagle" />
            </div>
            {navBar}
          </div>
          <TransientNotificationsContainer/>
        </div>
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  return {
    user: state.user,
    subscription: state.subscription
  }
};

export default connect(mapStateToProps)(Header)
