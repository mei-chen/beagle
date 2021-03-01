import React from 'react';
import { browserHistory, Link } from 'react-router';
import MaterialTitlePanel from './MaterialTitlePanel';
import Logo from './Logo';

import '../scss/sidebar.scss'

const SidebarContent = (props) => {
  return (
    <div className="aside">
      <div className="aside-header">
        <Logo />
      </div>
      <div className="aside-content">
        <div className="aside-links">
          <Link to="/dashboard" activeClassName="active"><i className="fa fa-bolt fa-fw"/> Analyze</Link>
          <Link to="/history/1" activeClassName="active"><i className="fa fa-history fa-fw"/> History</Link>
          <Link to="/settings" activeClassName="active"><i className="fa fa-cog fa-fw"/> Settings</Link>
        </div>
        <span className="aside-company">by <a href="http://beagle.ai" target="_blank">Beagle</a></span>
      </div>
    </div>
  );
};

SidebarContent.propTypes = {
  setSidebarOpen: React.PropTypes.func,
};

export default SidebarContent;
