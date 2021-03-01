import React from 'react';
import { connect } from 'react-redux';
import Time from 'react-time';
import Button from 'react-bootstrap/lib/Button';

/* Component Stylings */
require('./styles/Subscription.scss');   //stylings for component

const Subscription = React.createClass({
  handleSubscription() {
    window.location = './purchase';
  },

  renderContents() {
    const { subscription } = this.props;
    const currentSubscription = subscription.get('current_subscription');

    //Pre-existing users have no current subscription object be careful
    if (currentSubscription) {
      //'Free' user
      const isTrial = currentSubscription.get('is_trial');
      const daysRemaining = currentSubscription.get('display_days_remaining');
      if (isTrial) {
        let message;
        if (daysRemaining > 1) {
          message = <span> Your Beagle free trial has <strong>{daysRemaining}</strong> days remaining</span>;
        } else if (daysRemaining === 1) {
          message = <span>Today is your <strong>final</strong> trial day</span>;
        } else {
          message = (<span>Your Beagle free trial has expired. You may still collaborate on documents you have
            been invited to. To upload more documents you must sign up for the full version.</span>);
        }
        return (
          <div className="subscription-contents">
            <span className="free-trial-message">
              {message}
            </span>
            <Button onClick={this.handleSubscription} bsStyle="success">Get Beagle for just $4000/year</Button>
          </div>
        );
      //'Paid' user
      } else {
        return (
          <div className="subscription-contents">
            <span className="paid-trial-message">
              <div className="subscription-item">
                <span>Account Creation:
                  <strong> <Time locale="en" value={currentSubscription.get('start').split(' ')[0]} format="MMMM D, YYYY"/></strong>
                </span>
              </div>
              <div className="subscription-item">
                <span>Account Expiry: <strong><Time locale="en" value={currentSubscription.get('end').split(' ')[0]} format="MMMM D, YYYY"/></strong></span>
              </div>
              <div className="subscription-item">
                <span>Days Remaining: <strong>{daysRemaining}</strong></span>
              </div>
            </span>
          </div>
        )
      }
    } else { //END: Pre-existing users have no current subscription object be careful
      return (
        <div className="subscription-contents">
          <span className="paid-trial-message">
            <span className = "warning-sign"><i className="fa fa-exclamation-triangle" aria-hidden="true" /></span> No subscription is active at the moment
          </span>
        </div>
      )
    }
  },

  render() {
    return (
      <div className="settings-subscription">
        <span className="settings-subscription-title">Subscription</span>
        { this.renderContents() }
      </div>
    );
  }
});

const mapSubscriptionStateToProps = (state) => {
  return {
    subscription: state.subscription
  }
};

export default connect(mapSubscriptionStateToProps)(Subscription)
