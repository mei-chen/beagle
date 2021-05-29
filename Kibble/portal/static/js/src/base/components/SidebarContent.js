import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { hashHistory } from 'react-router';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import MaterialTitlePanel from 'base/components/MaterialTitlePanel';

import { sideBarItems } from 'base/constants/sidebar';
import { urls } from 'base/constants/constants';
/* eslint import/no-unresolved: [2, { ignore: ['\.scss$'] }]*/
import 'base/scss/SidebarContent.scss';
import { setActiveRootFolder, setActiveUrl } from 'base/redux/modules/sidebar';

const styles = {
  sidebar: {
    width: 256,
    height: 'calc(100% - 62px)', // full height without logo bar
  },
  sidebarLink: {
    display: 'block',
    padding: '20px',
    color: '#757575',
    textDecoration: 'none',
    cursor: 'pointer',
    borderBottom: '1px solid #eee',
  },
  secondaryLink: {
    display: 'block',
    padding: '20px 0px 20px 40px',
    color: '#757575',
    textDecoration: 'none',
    cursor: 'pointer',
    borderBottom: '1px solid #eee',
  },
  content: {
    float: 'left',
    height: '100%',
    width: '100%',
    backgroundColor: 'white',
    color: '#cecece',
  },
};


class SidebarContent extends React.Component {
  constructor(props) {
    super(props);
    this.currentLocationPath = () => hashHistory.getCurrentLocation().pathname;
    this.beagleLogo = <img src="/static/img/logo.png" height="25px" alt="Beagle"/>;
    this.style = props.style ? { ...styles.sidebar, ...props.style } : styles.sidebar;
    this.navTo = this.navTo.bind(this);
    this.TopLevelItem = this.TopLevelItem.bind(this);
    this.SubLevelItems = this.SubLevelItems.bind(this);
  }

  componentWillMount() {
    let currentUrl = this.currentLocationPath();
    if (currentUrl === '/') currentUrl = urls.LOCAL_FOLDER;
    this.props.setActiveUrl(currentUrl);
    for (const page of sideBarItems) {
      const afu = page.activeForUrls;
      if (!afu && page.url === currentUrl) {
        this.props.setActiveRootFolder(page.title);
        return
      } else if (afu && afu.indexOf(currentUrl) > -1) {
        this.props.setActiveRootFolder(page.title);
        return
      }
    }
  }

  navTo(page, rootFolder = null) {
    if (this.currentLocationPath() !== page) {
      hashHistory.push(page);
    }
    if (rootFolder) {
      this.props.setActiveRootFolder(rootFolder)
    }
    this.props.setActiveUrl(page);
    this.props.setSidebarOpen(false);
  };

  TopLevelItem({ title, url, subMenuItems, activeForUrls }) {
    const isActive = this.props.activeRootFolder === title;
    const className = !subMenuItems && isActive ? 'active' : '';
    const onClick = isActive ? () => {} : () => this.navTo(url, title);
    const SubLevelItems = this.SubLevelItems;
    return (
      <div>
        <a style={styles.sidebarLink} className={className} onClick={onClick}>
          { subMenuItems ?
            <i className="fal fa-chevron-down"></i> :
            <i className="fal fa-cog"></i>
          } {title}
        </a>
        <SubLevelItems
          activeForUrls={activeForUrls}
          subMenuItems={subMenuItems}
        />
      </div>
    )
  };

  SubLevelItems({ subMenuItems, activeForUrls }) {
    if (!subMenuItems) return null;
    if (activeForUrls.indexOf(this.currentLocationPath()) === -1) return null;
    return (
      <ReactCSSTransitionGroup
        transitionName="dropdown"
        transitionEnterTimeout={700}
        transitionLeaveTimeout={700}
        transitionAppear
        transitionAppearTimeout={200}>
        <div className="dropdown-list">
          {subMenuItems.map(item => {
            const isActive = item.url === this.props.activeUrl;
            const onClick = isActive ? () => {
            } : () => this.navTo(item.url);
            const className = isActive ? 'active' : '';
            return (
              <a style={styles.secondaryLink} className={className} onClick={onClick} key={item.title}>
                <i className="fal fa-minus"></i> {item.title}
              </a>
            )
          })}
        </div>
      </ReactCSSTransitionGroup>
    )
  };

  render() {
    const TopLevelItem = this.TopLevelItem;
    return (
      <MaterialTitlePanel title={this.beagleLogo} style={this.style}>
        <div style={styles.content} className="menu-container">
          { sideBarItems.map(page => (
            <TopLevelItem
              key={page.title}
              title={page.title}
              url={page.url}
              activeForUrls={page.activeForUrls}
              subMenuItems={page.subMenuItems}
            />
          )) }
          <div className="sidebarFooter">
            by <a href="https://beagleai.com/" title="Beagle.ai" target='_blank'>Beagle</a>
          </div>
        </div>
      </MaterialTitlePanel>
    )
  }
}

SidebarContent.propTypes = {
  style: PropTypes.shape({}),
  setSidebarOpen: PropTypes.func,
};

export default connect(
  state => ({
    activeRootFolder: state.global.sidebar.get('activeRootFolder'),
    activeUrl: state.global.sidebar.get('activeUrl')
  }),
  dispatch => bindActionCreators({
    setActiveRootFolder,
    setActiveUrl
  }, dispatch)
)(SidebarContent);
