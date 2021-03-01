var React = require('react');
var Reflux = require('reflux');
var classNames = require('classnames');
var OnClickOutside = require('react-onclickoutside');
var Crouton = require('react-crouton')
var $ = require('jquery');

var localStore = require('utils/localStore');

var UserStore = require('common/stores/UserStore');
var SubscriptionStore = require('common/stores/SubscriptionStore');
var ReportStore = require('report/stores/ReportStore');
var SharedUsers = require('report/components/SharedUsers');
var PersistentNotifications = require('common/components/PersistentNotifications');
var TransientNotificationsContainer = require('common/components/TransientNotifications')

require('./styles/Header.scss');   //stylings for component

const INTERCOM_ACTIVATOR = 'beagle-intercom';
const DISMISS_CROUTON = 'didDismissCrouton';


var Menu = React.createClass({

  mixins: [Reflux.connect(UserStore, 'user'), OnClickOutside],

  propTypes: {
    isActive: React.PropTypes.bool.isRequired,
  },

  getDefaultProps() {
    return {
      isActive: false
    };
  },

  componentDidUpdate(oldProps) {
    if (oldProps.isActive !== this.props.isActive) {
      Intercom('reattach_activator');
    }
  },

  menuToggle: function(event) {
    // create menu variables
    let slideoutMenu = $('.slideout-menu');
    let slideoutMenuWidth = $('.slideout-menu').width();

    // toggle open class
    slideoutMenu.toggleClass("open");

    // slide menu
    if (slideoutMenu.hasClass("open")) {
      slideoutMenu.animate({
        right: "0px"
      }, 250);
    } else {
      slideoutMenu.animate({
        right: -slideoutMenuWidth
      }, 250);
    }
  },

  handleClickOutside() {
    let slideoutMenu = $('.slideout-menu');

    if (slideoutMenu.hasClass("open")) {
      slideoutMenu.animate({
        right: "0px"
      }, 250);
    }
  },

  render() {
    var analysis = this.state.analysis;

    var menuButtom = (
      <div className="menu-toggle ignore-react-onclickoutside">
        <button type="button" className="navbar-toggle" onClick={this.menuToggle}>
          <span className="sr-only">Toggle navigation</span>
          <i className="fa fa-bars"></i>
        </button>
      </div>
    );

    var slideoutMenu;
    var displayName = '';

    if (this.state.user.username === undefined) {
      // no session active display sign in button
      slideoutMenu = (
        <div className="slideout-menu">
          <ul className="menu-list">
            <li><a href="/login">
              <i className="fa fa-user" /> Sign In
            </a></li>
            <li><a href="/account">
              <i className="fa fa-th" /> Your Documents
            </a></li>
            <li><a id={INTERCOM_ACTIVATOR}>
              <i className="fa fa-question" /> Chat With Us
            </a></li>
            <li><a href="http://docs.beagle.ai" target="_blank">
              <i className="fa fa-medkit" /> Manuals
            </a></li>
            <li><a href="/redeem-coupon">
              <i className="fa fa-ticket" /> Redeem Coupon
            </a></li>
          </ul>
        </div>
      );
    } else {
      // Display signed in user name + logout button
      var avatar = this.state.user.avatar;
      var username = this.state.user.username;
      var firstName = this.state.user.first_name || '';
      var lastName = this.state.user.last_name || '';
      var fullName = (firstName + ' ' + lastName).trim();
      displayName = fullName !== '' ? fullName : username;

      let avatarStyles = {
        backgroundImage: avatar ? `url('${avatar}')` : null
      }

      slideoutMenu = (
        <div className="slideout-menu">
          <ul className="menu-list">
            <li><a href="/account">
              <div style={avatarStyles} className="avatar" /> {displayName}
            </a></li>
            <li><a href="/account">
              <i className="fa fa-th" /> Your Documents
            </a></li>
            <li><a id={INTERCOM_ACTIVATOR}>
              <i className="fa fa-question" /> Chat With Us
            </a></li>
            <li><a href="http://docs.beagle.ai" target="_blank">
              <i className="fa fa-medkit" /> Manuals
            </a></li>
            <li><a href="/redeem-coupon">
              <i className="fa fa-ticket" /> Redeem Coupon
            </a></li>
            <li><a href="/logout">
              <i className="fa fa-sign-out" /> Sign out
            </a></li>
          </ul>
        </div>
      );
    }

    return (
      <div className="header-menu header-nav-item">
        {menuButtom}
        {slideoutMenu}
      </div>
    );
  }

});


var Header = React.createClass({

  mixins: [
    Reflux.connect(ReportStore, "analysis"),
    Reflux.connect(SubscriptionStore, 'subscription'),
  ],

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
      showCrouton: true,
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
    let isChrome = (window.browser && window.browser.chrome) || false;
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
    window.location = "/purchase";
  },

  goToGetStarted() {
    window.location = "/getstarted";
  },

  render() {
    var analysis = this.state.analysis;
    var crouton;
    if (this.state.showCrouton) {
       crouton = this.generateCrouton();
    }

    var additionalHeaderMessage;
    //Pre-existing users have no current subscription object be careful
    if (!!this.state.subscription.current_subscription) {
      var currentSubscription = this.state.subscription.current_subscription;
      var isTrial = currentSubscription.is_trial;
      if (isTrial) {
        var daysRemaining = currentSubscription.display_days_remaining;
        var message;
        if(daysRemaining > 1) {
          message = <span><strong>{daysRemaining}</strong> trial days remaining</span>;
        } else if (daysRemaining === 1) {
          message = <span><strong>final</strong> trial day</span>;
        } else {
          message = <span>trial has expired.</span>;
        }
        additionalHeaderMessage = (
          <div className="header-additional-message">
            <span onClick={this.handleSubscription} className="header-nav-item-link trial-link">{message}</span>
          </div>
        );
      }
    } else if (!UserStore.isPaidUser()) {
      additionalHeaderMessage = (
        <div className="header-additional-message">
          <span onClick={this.goToGetStarted} className="header-nav-item-link trial-link">
            <strong>Get started</strong>
          </span>
        </div>
      );
    }

    var notifications;
    if (UserStore.isLoggedIn()) {
      notifications = (
        <div className="header-notifications header-nav-item">
          <PersistentNotifications />
        </div>
      );
    }

    let headerClasses = classNames(
      'beagle-header',
      this.props.shouldShrink ? 'shrinkable' : null,
    );

    return (
      <div id="header" className={headerClasses}>
        <div className="header-wrap">
          <div className="header-left-nav">
            <SharedUsers uuid={analysis.uuid}
              collaborators={analysis.collaborators}
              owner={analysis.owner} />
          </div>
          <div className="header-right-nav">
            {notifications}
            <Menu />
          </div>
        </div>
        <TransientNotificationsContainer />
      </div>
    );
  }

});


module.exports = Header;
