import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import Sidebar from 'react-sidebar';
import MaterialTitlePanel from 'base/components/MaterialTitlePanel';
import SidebarContent from 'base/components/SidebarContent';
import Notify from 'Messages/components/Notify';
import IntercomButton from 'base/components/IntercomButton';
import NotificationLogTrigger from 'base/components/NotificationLogTriggerButton';

import 'base/scss/main.scss';

import { getLoggedUser } from 'base/redux/modules/user';
import { getProjects } from 'base/redux/modules/projects';

const styles = {
  sidebar: {
    color: 'white',
    width: 200,
    backgroundColor: 'white',
    zIndex: 3,
    overflowX: 'hidden',
    overflowY: 'auto'
  },
  contentHeaderMenuLink: {
    textDecoration: 'none',
    color: 'white',
    cursor: 'pointer',
    padding: 8,
  }
};

class SideBarComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      sidebarOpen: false,
      sidebarDocked: false
    };
    this.toggleOpen = this.toggleOpen.bind(this);
    this.onSetSidebarOpen = this.onSetSidebarOpen.bind(this);
    this.mediaQueryChanged = this.mediaQueryChanged.bind(this);
    this.renderHeaderContent = this.renderHeaderContent.bind(this);
  }

  componentWillMount() {
    const mql = window.matchMedia('(min-width: 800px)');
    mql.addListener(this.mediaQueryChanged);
    this.setState({
      mql,
      sidebarDocked: mql.matches
    });
  }

  componentDidMount() {
    // Load app-wide data (logged user, projects list)
    this.props.getLoggedUser();
    this.props.getProjects();
  }

  componentWillUnmount() {
    this.state.mql.removeListener(this.mediaQueryChanged);
  }

  onSetSidebarOpen(open) {
    this.setState({sidebarOpen: open});
  }

  mediaQueryChanged() {
    this.setState({sidebarDocked: this.state.mql.matches});
  }

  toggleOpen(e) {
    this.setState({sidebarOpen: !this.state.sidebarOpen});
    if (e) {
      e.preventDefault();
    }
  }

  renderHeaderContent() {
    const { user } = this.props;
    const isLoggedIn = user.get('isLoggedIn');
    const details = user.get('details');

    return (
      <div className="header clearfix">
        {!this.state.sidebarDocked && (
          <a
            href="#"
            onClick={this.toggleOpen}
            style={styles.contentHeaderMenuLink}>
            <i className="fa fa-bars" />
          </a>
        )}
        <span>Kibble</span>

        { isLoggedIn && (
          <div className="account">
            <i className="fa fa-user-circle" />
            <span className="account-email">
              <span className="account-email-overflow">{ details.get('username') }</span>
            </span>
            <a
              href="/accounts/logout"
              className="account-sign-out">
              <i className="fal fa-sign-out"></i>
            </a>
          </div>
        )}

      </div>
    );
  }

  render() {
    const sidebar = <SidebarContent setSidebarOpen={this.onSetSidebarOpen} />;

    return (
      <Sidebar
        sidebar={sidebar}
        open={this.state.sidebarOpen}
        docked={this.state.sidebarDocked}
        styles={styles}
        shadow={false}
        sidebarClassName="sidebar"
        onSetOpen={this.onSetSidebarOpen}>
        <MaterialTitlePanel title={this.renderHeaderContent()}>
          { this.props.children }
        </MaterialTitlePanel>
        <Notify />
        <IntercomButton />
        <NotificationLogTrigger />
      </Sidebar>
    );
  }
}

SideBarComponent.propTypes = {
  children: PropTypes.shape({}).isRequired
};

const mapStateToProps = state => {
  return {
    user: state.global.user
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getLoggedUser, getProjects
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(SideBarComponent);
