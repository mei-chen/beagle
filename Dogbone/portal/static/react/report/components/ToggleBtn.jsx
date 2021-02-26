import React from 'react';
import classNames from 'classnames';


const ToggleBtn = React.createClass({

  onClick(evt) {
    this.props.onClick(evt);
  },

  render() {
    const classes = classNames(
      'toggle-btn',
      this.props.isActive ? 'active' : null,
      this.props.className ? this.props.className : null
    );

    return (
      <a className={classes} onClick={this.onClick}>
        {this.props.children}
      </a>
    );
  }

});


module.exports = ToggleBtn;
