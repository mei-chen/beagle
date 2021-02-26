import { connect } from 'react-redux';
import io from 'socket.io-client';
import React from 'react';
import Time from 'react-time'
import classNames from 'classnames';
import OnClickOutside from 'react-onclickoutside';

import log from 'utils/logging';
import {
  getFromServer,
  markRead,
  markAllRead,
  updatePageNumber
} from 'common/redux/modules/persistentnotification';

require('./styles/Notifications.scss');

const socket = io(window.socketServerAddr);

class BadgeWithDocumentTitle extends React.Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    this.updateHeader();
  }

  componentDidUpdate(oldProps) {
    if (oldProps.unreadCount !== this.props.unreadCount) {
      this.updateHeader();
    }
  }

  updateHeader() {
    const { unreadCount, standardHeader } = this.props;

    if (unreadCount > 0) {
      document.title = `(${unreadCount}) ${standardHeader}`;
    } else {
      document.title = standardHeader;
    }
  }

  render() {
    const { unreadCount } = this.props;
    const badgeClasses = classNames(
      'badge',
      unreadCount > 0 ? 'active' : null
    );
    return <span className={badgeClasses} />;
  }

}

BadgeWithDocumentTitle.defaultProps = {
  unreadCount: 0
}

BadgeWithDocumentTitle.propTypes = {
  unreadCount: React.PropTypes.number.isRequired
}

const NotificationComponent = React.createClass({

  propTypes: {
    notification: React.PropTypes.object.isRequired,
    hideDropdown: React.PropTypes.func.isRequired,
  },

  markAsRead() {
    const { notification, dispatch } = this.props;
    dispatch(markRead(notification.get('id')));
  },

  onClickNotification() {
    this.markAsRead();
    this.props.hideDropdown();
  },

  render() {
    var notif = this.props.notification;
    var notifType = notif.get('target_type');

    var avatarURL;
    if (notifType === 'externalinvite') {
      var target = notif.get('target')
      var actor = notif.get('actor');
      avatarURL = target ? target.getIn(['invitee', 'avatar']) : actor.get('avatar');
    }
    else if (notifType === 'user') {
      avatarURL = notif.getIn(['actor', 'avatar']);
    }
    else if (notifType === 'sentence' || notifType === 'document') {
      avatarURL = notif.getIn(['actor', 'avatar']);
    }
    else {
      log.error('unencountered notification type', notif.toJS());
      avatarURL = notif.getIn(['actor', 'avatar']);
    }

    var avatar;
    if (avatarURL) {
      avatar = <div className="avatar" style={{ backgroundImage: `url(${avatarURL})` }} />
    }

    var indicatorClasses = classNames(
      'indicator',
      notif.get('read') ? 'read' : 'unread'
    );

    return (
      <div className="notif">
        <div className="read-indicator" onClick={this.markAsRead}>
          <span className={indicatorClasses}/>
        </div>
        <a className="content"
          href={notif.get('url')}
          onClick={this.onClickNotification}>
          {avatar}
          <div className="info">
            <div className="text"> {notif.get('suggested_display')} </div>
            <div className="time">
              <Time value={notif.get('timestamp')} titleFormat="YYYY/MM/DD HH:mm" relative/>
            </div>
          </div>
        </a>
      </div>
    );
  }
});

const Notification = connect()(NotificationComponent)


const LoadMoreComponent = React.createClass({

  getInitialState() {
    return {
      isLoading: false
    }
  },

  loadMore() {
    const { dispatch, notifs } = this.props;

    dispatch(updatePageNumber(notifs.get('page') + 1));
    dispatch(getFromServer());
  },

  render() {
    const { notifs } = this.props;
    const spinnerClasses = classNames(
      'spinner',
      'fa fa-spinner fa-spin',
      notifs.get('isLoading') ? 'active' : null
    );
    return (
      <button className="load-more" onClick={this.loadMore}>
        Load more
        <i className={spinnerClasses} style={{ marginTop: '2px' }}/>
      </button>
    );
  }

});

const mapLoadMoreComponentStateToProps = (state) => {
  return {
    notifs: state.persistentnotification,
  }
};

const LoadMore = connect(mapLoadMoreComponentStateToProps)(LoadMoreComponent)


const NotificationDropdownComponent = React.createClass({

  propTypes: {
    unreadCount: React.PropTypes.number.isRequired,
    hasMorePages: React.PropTypes.bool.isRequired,
    hideDropdown: React.PropTypes.func.isRequired,
    notifications: React.PropTypes.object.isRequired, // Immutable.List
  },

  getInitialState() {
    return {
      showUnreadOnly: false
    };
  },

  handleClickOutside() {
    this.props.hideDropdown();
  },

  toggleShowUnread() {
    this.setState({ showUnreadOnly: !this.state.showUnreadOnly });
  },

  markAllRead() {
    const { dispatch } = this.props;
    dispatch(markAllRead());
  },

  render() {
    var notifs = this.props.notifications;
    var displayNotifs = notifs.toArray();
    if (this.state.showUnreadOnly) {
      displayNotifs = displayNotifs.filter(n => n.get('read') === false);
    }

    var notificationContents;
    if (displayNotifs.length > 0) {
      notificationContents = [];
      displayNotifs.forEach(notif => notificationContents.push(
        <Notification
          key={notif.get('id')}
          notification={notif}
          hideDropdown={this.props.hideDropdown}
        />
      ));
    } else {
      notificationContents = (
        <span className="notif no-data">No notifications</span>
      );
    }

    var showingUnreadOnly = this.state.showUnreadOnly;
    var totalUnreadCount = this.props.unreadCount;
    var loadedUnreadCount = notifs.filterNot(n => n.get('read')).size;

    var loadMore;
    if (
      this.props.hasMorePages &&
      !(showingUnreadOnly && totalUnreadCount === loadedUnreadCount)
    ) {
      loadMore = <LoadMore />;
    } else {
      loadMore = <span className="notif no-data">There are no more notifications to load.</span>;
    }

    var toggles;
    const WHY_IS_THIS_HERE = true;
    if (WHY_IS_THIS_HERE) {
      var showUnreadClasses = classNames(
        'show-unread-only',
        showingUnreadOnly ? 'active' : null
      );
      toggles = (
        <div className="menu-toggles">
          <button
            className={showUnreadClasses}
            onClick={this.toggleShowUnread}
          >
            Show unread only
          </button>
          <button
            className="mark-all-read"
            onClick={this.markAllRead}
            disabled={totalUnreadCount === 0}
          >
            Mark all as read
          </button>
        </div>
      );
    }

    return (
      <div className="header-dropdown notification-dropdown">
        {toggles}
        <div className="scrollable-container">
          <div className="contents">
            {notificationContents}
            {loadMore}
          </div>
        </div>
        <div className="dropdown-arrow" />
      </div>
    );
  }
});

const NotificationDropdown = connect()(OnClickOutside(NotificationDropdownComponent));

const Notifications = React.createClass({

  getInitialState() {
    return {
      dropdownOpen: false,
      standardHeader: document.title
    };
  },

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(getFromServer());
    this.socketListener();
  },

  socketListener() {
    const { dispatch } = this.props;

    socket.on('message', msg => {
      const type = msg.notif;
      if (type === 'ACTIVITY_UPDATE') {
        dispatch(getFromServer());
      }
    });
  },

  showDropdown() {
    document.body.classList.add('no-scroll');
    this.setState({ dropdownOpen: true });
  },

  hideDropdown() {
    document.body.classList.remove('no-scroll');
    this.setState({ dropdownOpen: false });
  },

  toggleDropdown() {
    if (this.state.dropdownOpen) {
      this.hideDropdown();
    } else {
      this.showDropdown();
    }
  },

  render() {
    const { notifs } = this.props;

    if (!notifs.get('isInitialized')) {
      return (
        <div className="beagle-notifications">
          <div className="bell-icon ignore-react-onclickoutside">
            <i className="fa fa-bell" />
          </div>
        </div>
      )
    }

    const notifications = notifs.get('objects');
    const unreadCount = notifs.getIn(['meta', 'unread_count']);
    const pageCount = notifs.getIn(['meta', 'pagination', 'page_count']);
    const currentPage = notifs.getIn(['meta', 'pagination', 'page']);

    const dropdown = (
        this.state.dropdownOpen ?
        (
          <NotificationDropdown
            unreadCount={unreadCount}
            hasMorePages={currentPage < pageCount-1}
            hideDropdown={this.hideDropdown}
            notifications={notifications}
          />
        ) :
        null
    );

    return (
      <div className="beagle-notifications">
        <div className="bell-icon ignore-react-onclickoutside"
          onClick={this.toggleDropdown}>
          <i className="fa fa-bell" />
          <BadgeWithDocumentTitle
            unreadCount={unreadCount}
            standardHeader={this.state.standardHeader}
          />
        </div>
        {dropdown}
      </div>
    );
  }

});


const mapStateToProps = (state) => {
  return {
    notifs: state.persistentnotification,
  }
};

export default connect(mapStateToProps)(Notifications)
