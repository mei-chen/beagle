import React from 'react';
import { browserHistory, Link } from 'react-router'
import MaterialTitlePanel from './MaterialTitlePanel';

const styles = {
  sidebar: {
    width: 200,
    height: '90%',
  },
  sidebarLink: {
    display: 'block',
    padding: '10px 0px',
    color: '#757575',
    cursor: 'pointer',
    textDecoration: 'none',
  },
  sidebarLinkActive: {
    color: '#1a1a1a'
  },
  divider: {
    margin: '26px 50px 8px 0px',
    height: 1,
    backgroundColor: '#757575',
  },
  content: {
    padding: '20px',
    height: 'calc(100% - 62px)',
    backgroundColor: 'white',
    color: '#cecece',
  },
  menuIcon: {
    color: '#333',
  },
};

const SidebarContent = (props) => {
  const style = props.style ? {...styles.sidebar, ...props.style} : styles.sidebar;

  const beagle_logo = (<img src="/static/img/logo.svg" alt="Beagle"/>);

  return (
    <MaterialTitlePanel title={beagle_logo} style={style}>
      <div style={styles.content}>
        <Link to="/experiments" style={styles.sidebarLink} activeStyle={styles.sidebarLinkActive}>
          <span style={styles.menuIcon}><i className="fa fa-lightbulb fa-fw"></i></span> Experiments
        </Link>
        <Link to="/datasets" style={styles.sidebarLink} activeStyle={styles.sidebarLinkActive}>
          <span style={styles.menuIcon}><i className="fa fa-database fa-fw"></i></span> Datasets
        </Link>
        <Link to="/tasks" style={styles.sidebarLink} activeStyle={styles.sidebarLinkActive}>
          <span style={styles.menuIcon}><i className="fa fa-pen-alt fa-fw"></i></span> Labeling
        </Link>
        <div style={styles.divider} />
        by <a href="http://beagle.ai" title="Beagle.ai">Beagle</a>
      </div>
    </MaterialTitlePanel>
  );
};

SidebarContent.propTypes = {
  style: React.PropTypes.object,
  setSidebarOpen: React.PropTypes.func,
};

export default SidebarContent;
