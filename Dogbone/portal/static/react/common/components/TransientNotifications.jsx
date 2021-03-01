import React from 'react';
import { connect } from 'react-redux';
import Crouton from 'react-crouton';
import { includes } from 'lodash';
import invariant from 'invariant';
import uuidV4 from 'uuid/v4';

import Toast from './Toast';

require('./styles/Header.scss');
require('./styles/Crouton.scss');


const TransientNotificationsContainer = React.createClass({
  getInitialState() {
    return {
      hidden: false
    };
  },

  componentWillReceiveProps(nextProps) {
    this.setState({ hidden: nextProps.notifications.count() === 0 });
  },

  addNotification(notification) {
    var { style } = notification;
    invariant(
      includes(['toast', 'crouton'], style),
      `'${style} is not a supported notification style. See TransientNotifications.jsx`
    );
  },

  hideCrouton() {
    this.setState({ hidden: true });
  },

  render() {
    const { notifications } = this.props;
    return (
      <div className="beagle-notifications-container">
        <Toast ref="toast" />
        {
          notifications.toJS().map(msg => {
            return (
              <Crouton
                id={uuidV4()}
                hidden={this.state.hidden}
                message={msg.msg}
                type={msg.type}
                timeout={5000*60}
                onDismiss={this.hideCrouton}
              />
            )
          })
        }
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    notifications: state.transientnotification.get('notifications').filter(x => x.get('style') === 'crouton')
  }
};

export default connect(mapStateToProps)(TransientNotificationsContainer)
