var React = require('react');
var Reflux = require('reflux');
var Button = require('react-bootstrap/lib/Button');

require('./styles/SubscriptionSection.scss');   //stylings for component

/* This component offers the user a chance to pay for a subscription
or should they have not yet undergone a free trial, offers that */

var SubscriptionSection = React.createClass({

  propTypes: {
    hasHadTrial: React.PropTypes.bool
  },

  onTrialClick() {
    window.location.href = "/purchase";
  },

  onPaymentClick() {
    window.location.href = "/purchase";
  },

  renderCTA() {
    var trialButton = this.props.hasHadTrial ? null : <Button onClick={this.onTrialClick}> 7 Day FREE Trial </Button>;
    return (
      <div className="call-to-action">
        <div className="button-panel">
          <Button onClick={this.onPaymentClick}>Purchase</Button>
          {trialButton}
        </div>
      </div>
    );
  },

  render() {
    var explanationL1 = "In order to upload documents of your own,";
    var explanationL2 = " you must purchase Beagle";
    var message = !!this.props.hasHadTrial ? "." : ", or trial Beagle for free for 7 days.";
    return (
      <div className="subscription-section">
        <div className="explanation">
          {explanationL1}<br/>
          {explanationL2}
          {message}
        </div>
        {this.renderCTA()}
      </div>
    );
  }

});

module.exports = SubscriptionSection;