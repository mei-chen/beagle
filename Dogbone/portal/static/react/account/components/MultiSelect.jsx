import React, { Component, PropTypes } from 'react';
import classNames from 'classnames';

import './styles/MultiSelect.scss';

class MultiSelect extends Component {
  constructor(props) {
    super(props);
    this._renderOptions = this._renderOptions.bind(this);
    this._toggleDrop = this._toggleDrop.bind(this);
    this._handleChange = this._handleChange.bind(this);
    this._getPlaceholder = this._getPlaceholder.bind(this);
    this.state = {
      selected: props.selected,
      isOpen: false
    }
  }

  componentWillReceiveProps(nextProps) {
    this.setState({ selected: nextProps.selected });
  }

  _renderOptions(options) {
    const { optionIcon } = this.props;
    const { selected } = this.state;

    if (options.length === 0) {
      return <span>No options available...</span>
    }

    return options.map((option, i) => {
      const active = selected.indexOf(option) !== -1;
      const optionClassNames = classNames('multiselect-option', {
        'multiselect-option--checked': active
      })

      return (
        <li
          key={i}
          className={optionClassNames}
          onClick={() => this._handleChange(!active, option)}>
          <span className="multiselect-icon">
            <i className={active ? 'fa fa-check' : optionIcon} />
          </span>
          <span className="multiselect-text">{ option }</span>
        </li>
      )
    })
  }

  _toggleDrop() {
    this.setState({ isOpen: !this.state.isOpen });
  }

  _handleChange(status, value) {
    const { onChange } = this.props;
    const { selected } = this.state;
    let newSelected = Object.assign([], selected);

    if (!status) {
      newSelected = selected.filter(x => x !== value);
    } else {
      newSelected.push(value);
    }

    this.setState({ selected: newSelected })
    onChange(newSelected);
  }

  _getPlaceholder() {
    const { placeholder, entity } = this.props;
    const { selected } = this.state;
    const [ singular, plural ] = entity;

    if (!selected.length) return placeholder;

    return selected.length === 1 ? `1 ${singular}` : `${selected.length} ${plural}`;
  }

  render() {
    const { options, className } = this.props;
    const { isOpen } = this.state;

    const multiselectClassNames = classNames('multiselect', {
      'multiselect--open': isOpen,
      [className]: className
    })

    return (
      <div className={multiselectClassNames}>
        <div
          className="multiselect-btn"
          onClick={this._toggleDrop}>
          { this._getPlaceholder() }
        </div>

        { isOpen && (
          <ul className="multiselect-options">
            { this._renderOptions(options) }
          </ul>
        ) }
      </div>
    )
  }
}

MultiSelect.propTypes = {
  className: PropTypes.string,
  options: PropTypes.array.isRequired,
  selected: PropTypes.array.isRequired,
  placeholder: PropTypes.string.isRequired,
  entity: PropTypes.array.isRequired, // [singular, plural]
  optionIcon: PropTypes.string,
  onChange: PropTypes.func.isRequired
};

MultiSelect.defaultProps = {
  placeholder: 'All options',
  entity: ['option', 'options'],
  optionIcon: 'fa fa-circle-thin'
};

export default MultiSelect;
