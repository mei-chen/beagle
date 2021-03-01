import React from 'react';

require('./styles/SideMenuButton.scss');   //stylings for component

var SideMenuButton = React.createClass({

  getInitialState() {
    return {
      hover : false,
    };
  },

  render() {
    var active = this.props.active ? 'active' : '';
    var styles = 'sidemenu-button ' + active;
    var chevron = this.props.active ? (
        <span className="active-chevron">
          <i className="fa fa-chevron-right" />
        </span>
      ) : null;

    return (
      <div className={styles} onClick={this.props.onClick}>
        {this.props.children}
        {chevron}
      </div>
    );
  }

});

module.exports = SideMenuButton;
