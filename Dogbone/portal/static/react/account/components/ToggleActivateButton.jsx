import React from 'react';
import classNames from 'classnames';

export const ToggleActivateButton = React.createClass({
  render() {
    const toggle_status = this.props.active ? 'on' : 'off';
    const toggleIconClass = classNames('fa', 'fa-toggle-' + toggle_status, toggle_status);

    return (
      <span className="toggleActiveButton" onClick={this.props.onClick}>
        <i className={toggleIconClass} />
      </span>
    );
  }
});

export default ToggleActivateButton;
