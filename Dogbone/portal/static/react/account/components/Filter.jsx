import React, { Component, PropTypes } from 'react';
import classNames from 'classnames';
import OnClickOutside from 'react-onclickoutside';

import './styles/Filter.scss';

class Filter extends Component {
  constructor(props) {
    super(props);
    this._handleClick = this._handleClick.bind(this);
    this.state = {
      isOpen: false
    }
  }

  handleClickOutside() {
    this.setState({ isOpen: false });
  }

  _handleClick() {
    const { children, onClick } = this.props;

    // if droppable
    children && this.setState({ isOpen: !this.state.isOpen })

    onClick && onClick();
  }

  render() {
    const { children, icon, title, className, active } = this.props;
    const { isOpen } = this.state;
    const filterClassName = classNames('filter', {
      'filter--active': active || isOpen,
      [className]: className
    })

    return (
      <div className={filterClassName}>
        <div
          className="filter-icon"
          onClick={this._handleClick}>
          <i className={icon} title={title} />
        </div>

        { isOpen && (
          <div className="filter-drop">{ children }</div>
        ) }
      </div>
    )
  }
}

Filter.propTypes = {
  icon: PropTypes.string.isRequired,
  title: PropTypes.string,
  active: PropTypes.bool,
  className: PropTypes.string,
  children: PropTypes.object, // drop
  onClick: PropTypes.func
};

Filter.defaultTypes = {
  icon: 'fa fa-filter'
};

export default OnClickOutside(Filter);
