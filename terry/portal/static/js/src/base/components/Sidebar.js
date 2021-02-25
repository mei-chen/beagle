import React, { Component, PropTypes } from 'react';
import { Link } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import Sidebar from 'react-sidebar';
import MaterialTitlePanel from './MaterialTitlePanel';
import SidebarContent from './SidebarContent';
import Footer from './Footer';
import IntercomButton from './IntercomButton';
import Logo from './Logo';

import '../scss/main.scss';

import { getFromServer } from 'base/redux/modules/user';

const styles = {
  sidebar: {
    color: 'white',
    width: 200,
    backgroundColor: 'white',
    boxShadow: 'rgba(0, 0, 0, 0.14902) 2px 2px 4px',
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
    const mql = window.matchMedia('(min-width: 870px)');
    mql.addListener(this.mediaQueryChanged);
    this.setState({
      mql,
      sidebarDocked: mql.matches
    });
  }

  componentDidMount() {
    this.props.getFromServer();
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
    const { user, isPermalink, isHidden } = this.props;
    const isLoggedIn = user.get('isLoggedIn');
    const details = user.get('details');

    return (
      <div className="header clearfix">
        {!this.state.sidebarDocked && !isHidden && (
          <a
            href="#"
            onClick={this.toggleOpen}
            style={styles.contentHeaderMenuLink}>
            <i className="fa fa-bars" />
          </a>
        )}

        { isPermalink && (
          <Logo white />
        ) }

        { isLoggedIn && !isPermalink && (
          <div className="account">
            <a href="/settings" className="account-user">
              <i className="fa fa-user-circle" />
              <span className="account-email">
                <span className="account-email-overflow">{ details.get('username') }</span>
              </span>
            </a>
            <a href="/accounts/logout"
               className="account-sign-out"
               title="Sign out">
              <i className="fa fa-sign-out"></i>
            </a>
          </div>
        )}

      </div>
    );
  }

  render() {
    const { isHidden } = this.props
    const sidebar = <SidebarContent setSidebarOpen={this.onSetSidebarOpen} />;

    return (
      <Sidebar
        sidebar={sidebar}
        open={isHidden ? false : this.state.sidebarOpen}
        docked={isHidden ? false : this.state.sidebarDocked}
        styles={styles}
        shadow={false}
        sidebarClassName="sidebar"
        onSetOpen={this.onSetSidebarOpen}>
        <MaterialTitlePanel title={this.renderHeaderContent()}>
          { this.props.children }
        </MaterialTitlePanel>
        <Footer />
        <IntercomButton />
      </Sidebar>
    );
  }
}

SideBarComponent.propTypes = {
  children: PropTypes.object.isRequired,
  isHidden: PropTypes.bool,
  isPermalink: PropTypes.bool
};

const mapStateToProps = state => {
  return {
    user: state.user
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(SideBarComponent);
