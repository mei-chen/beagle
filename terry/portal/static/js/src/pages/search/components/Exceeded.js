import React, { PropTypes } from 'react';
import { Map } from 'immutable';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Subscription from 'base/components/Subscription';

const Exceeded = ({ user }) => {
  const details = user.get('details');
  const subscription = details.get('subscription');
  const publicReports = details.get('public_reports_count');
  const privateReports = details.get('private_reports_count');

  return (
    <div className="exceeded">
      <img
        src="/static/img/empty-bowl.png"
        className="exceeded-image" />
      <h3 className="exceeded-title">You reached the limit of your current subscription</h3>
      { !!subscription && (
        <Subscription
          hasSubscription={!!subscription}
          plan={subscription.get('name')}
          expires={subscription.get('expires')}
          repos={{
            public: publicReports,
            private: privateReports
          }} />
      ) }
    </div>
  )
};

Exceeded.propTypes = {
  user: PropTypes.instanceOf(Map).isRequired
};

const mapStateToProps = state => {
  return {
    user: state.user
  }
}

export default connect(mapStateToProps)(Exceeded);

