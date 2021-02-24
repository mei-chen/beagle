import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import Sidebar from 'react-sidebar';
import MaterialTitlePanel from './MaterialTitlePanel';
import SidebarContent from './SidebarContent';
import Footer from './Footer';
import IntercomButton from './IntercomButton';

import '../scss/main.scss';

import { getFromServer } from 'base/redux/modules/user';

const styles = {
  sidebar: {
    color: 'white',
    width: 200,
    backgroundColor: 'white',
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
        <span>Spot</span>

        { isLoggedIn && (
          <div className="account">
            <i className="fa fa-user" />
            <span className="account-email">
              <span className="account-email-overflow">{ details.get('email') || details.get('username') }</span>
            </span>
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
        shadow={true}
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
  isHidden: PropTypes.bool
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
