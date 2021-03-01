import React from 'react';
import { connect } from 'react-redux';
import classNames from 'classnames';
import ReactTransitionGroup from 'react-addons-css-transition-group';
import uuidV4 from 'uuid/v4';

// App
import { removeNotification } from 'common/redux/modules/transientnotification';

require('./styles/Toast.scss');

const Toast = React.createClass({

  getDefaultProps() {
    return {
      timeout: 5000
    };
  },

  shouldComponentUpdate(nextProps) {
    // Only update when the notifications list are not equal
    return !this.props.notifications.equals(nextProps.notifications);
  },

  timeouts: {}, // A HACK AND IT'S NOT PART OF THE REACT FLOW BUT OUT OF OPTIONS

  startAutoDismiss(id) {
    const timeoutID = setTimeout(
      () => this.dismissNotification(id),
      this.props.timeout
    );
    this.timeouts[id] = timeoutID;
  },

  stopAutoDismiss(id) {
    const timeoutID = this.timeouts[id];
    clearTimeout(timeoutID);
    delete this.timeouts[id];
  },

  dismissNotification(id) {
    if (!this.timeouts[id]) return;
    const { dispatch } = this.props;
    dispatch(removeNotification(id));
    delete this.timeouts[id];
  },

  onMouseOver(msg) {
    this.stopAutoDismiss(msg.uuid);
  },

  onMouseOut(msg) {
    this.startAutoDismiss(msg.uuid);
  },

  renderToasts() {
    const { notifications } = this.props;
    return notifications.toJS().map(msg => {
      this.startAutoDismiss(msg.uuid);

      const toastClasses = classNames('toast', `toast-${msg.type}`);

      const closeBtn = (
        <span
          key={uuidV4()}
          className="close close-btn"
          style={{ zIndex: 9999 }}
          onClick={() => {
            this.timeouts[msg.uuid] = true;
            this.dismissNotification(msg.uuid)
          }}>
          <i className="fa fa-times" />
        </span>
      );

      let linkOrText;
      if (msg.url) {
        linkOrText = <a href={msg.url}>{msg.msg}</a>;
      } else {
        linkOrText = msg.msg;
      }

      return (
        <div key={msg.uuid}>
          <div
            className={toastClasses}
            onMouseOver={() => this.onMouseOver(msg)}
            onMouseOut={() => this.onMouseOut(msg)}>
            {closeBtn}
            {linkOrText}
          </div>
          <div className="toast-spacer"/>
        </div>
      );
    });
  },

  render() {
    // see http://khan.github.io/react-components/#timeout-transition-group
    return (
      <div className="beagle-toast-container">
        <ReactTransitionGroup
          transitionName="toast"
          transitionEnterTimeout={300}
          transitionLeaveTimeout={300}>
          { this.renderToasts() }
        </ReactTransitionGroup>
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    notifications: state.transientnotification.get('notifications').filter(x => x.get('style') === 'toast')
  }
};

export default connect(mapStateToProps)(Toast)
