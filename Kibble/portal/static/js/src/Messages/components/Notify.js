import React from "react";
import { connect } from "react-redux";
import { bindActionCreators } from 'redux';
import Notifications from 'react-notification-system-redux';
import PropTypes from 'prop-types';
import ImmutablePropTypes from 'react-immutable-proptypes';

import { showNotification } from "Messages/actions";
import { MODULE_NAME } from "Messages";
import { MAX_VISIBLE_MESSAGES } from "Messages/constants";


class Container extends React.Component {

  componentWillReceiveProps(nextProps) {
    const {notifications, queue} = nextProps;
    if (notifications.length < MAX_VISIBLE_MESSAGES && queue.size) {
      const item = queue.get(0);
      this.props.showNotification(item.message, item.level);
    }
  }

  render() {
    const {notifications} = this.props;

    const style = {
      NotificationItem: { // Override the notification item
        DefaultStyle: { // Applied to every notification, regardless of the notification level
          wordBreak: 'break-word',
        },
      }
    };

    return (
      <Notifications notifications={notifications} style={style} />
    );
  }
}

Container.contextTypes = {
  store: PropTypes.object
};

Container.propTypes = {
  notifications: PropTypes.array,
  queue: ImmutablePropTypes.listOf(PropTypes.shape({
    message: PropTypes.object,
    level: PropTypes.string
  })),
};


const mapStateToProps = (state) => {
  return {
    notifications: state.notifications,
    queue: state[ MODULE_NAME ]
  };
};


const mapDispatchToProps = dispatch => bindActionCreators({
    showNotification
}, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(Container);
