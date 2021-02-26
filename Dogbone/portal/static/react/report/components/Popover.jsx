import _ from 'lodash';
import React from 'react';
import classNames from 'classnames';
require('./styles/Popover.scss');

var PopoverOption = React.createClass({

  propTypes: {
    option: React.PropTypes.object.isRequired,
    onSelectOption: React.PropTypes.func.isRequired,
  },

  onSelectOption() {
    this.props.onSelectOption(this.props.option);
  },

  render() {
    var checkStyle = classNames(
      { 'fa fa-check' : this.props.option.isCurrent }
    );

    var optionStyle = classNames(
      { 'selected' : this.props.option.isCurrent }
    );

    return (
      <li>
        <div className="row" onClick={this.onSelectOption}>
          <div className="check">
            <i className={checkStyle}/>
          </div>
          <div className="option-name">
            <span className={optionStyle}>{this.props.option.display}</span>
          </div>
        </div>
      </li>
    )
  }
});

var Popover = React.createClass({

  propTypes: {
    disableSortSelectMode: React.PropTypes.func.isRequired,
    options: React.PropTypes.array.isRequired,
    type: React.PropTypes.string.isRequired,
    onSelectOption: React.PropTypes.func.isRequired,
  },

  onSelectOption(option) {
    this.props.onSelectOption(option);
  },

  render() {
    var options = this.props.options;
    var optionsList = _.map(options, o => {
      return <PopoverOption option={o} onSelectOption={this.onSelectOption}/>
    });

    //apply the type
    var style = {};
    style[this.props.type] = true;
    var positionStyle = classNames(
      'drop-popover',
      style
    );

    return (
      <div className={positionStyle}>
        <div className="popover-header">
          <span>{this.props.type}</span>
          <div className="close-icon" onClick={this.props.disableSortSelectMode}><i className="fa fa-times" /></div>
        </div>
        <div className="popover-body">
          <ul>
            {optionsList}
          </ul>
        </div>
      </div>
    )
  }
});

module.exports = Popover;