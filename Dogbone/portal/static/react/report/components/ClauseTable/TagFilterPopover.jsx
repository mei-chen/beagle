import React from 'react';
import classNames from 'classnames';
import OnClickOutside from 'react-onclickoutside';
import uuidV4 from 'uuid/v4';

require('./styles/TagFilterPopover.scss');

var PopoverOption = React.createClass({

  propTypes: {
    option: React.PropTypes.object.isRequired,
    onSelectOption: React.PropTypes.func.isRequired,
  },

  onSelectOption() {
    this.props.onSelectOption(this.props.option);
  },

  render() {
    var checkStyle = classNames({
      'fa fa-check': this.props.option.isCurrent
    });

    var optionStyle = classNames({
      'selected': this.props.option.isCurrent
    });

    var icon;
    switch (this.props.option.type) {
    case 'K':
      icon = classNames({
        'fa fa-bookmark' : true,
      });
      break;

    case 'A':
      icon = classNames({
        'fa fa-lightbulb' : true,
      });
      break;

    case 'S':
      icon = classNames({
        'fa fa-lightbulb' : true,
      });
      break;

    case 'M':
      icon = classNames({
        'no-icon' : true,
      });
      break;
    }

    return (
      <div className="row" onClick={this.onSelectOption}>
        <div className="check">
          <i className={checkStyle}/>
        </div>
        <div className="option-name">
          <span className={optionStyle}><span className={icon}/>{this.props.option.display}</span>
        </div>
      </div>
    );
  }
});

var TagFilterPopover = OnClickOutside(React.createClass({

  propTypes: {
    disableSortSelectMode: React.PropTypes.func.isRequired,
    options: React.PropTypes.array.isRequired,
    type: React.PropTypes.string.isRequired,
    onSelectOption: React.PropTypes.func.isRequired,
  },

  getInitialState() {
    return {
      query: '',
      inputFocus: false
    };
  },

  onSelectOption(option) {
    this.props.onSelectOption(option);
  },

  onQueryKeyDown(e) {
    var query = e.target.value;
    this.setState({ query: query });
  },

  onInputFocus() {
    this.setState({ inputFocus: true });
  },

  onInputBlur() {
    this.setState({ inputFocus: false });
  },

  handleClickOutside() {
    this.props.disableSortSelectMode();
  },

  render() {
    //left options
    var options = this.props.options;
    options = options.filter(o => o.display.toLowerCase().indexOf(this.state.query.toLowerCase()) > -1);
    var optionsList = options.map(o => {
      return <PopoverOption key={uuidV4()} option={o} onSelectOption={this.onSelectOption}/>;
    });
    //apply the type
    var style = {};
    style[this.props.type] = true;
    var positionStyle = classNames(
      'ignore-react-onclickoutside',
      'drop-popover',
      style
    );

    var searchIconStyle = classNames(
      'search-icon',
      { 'active': this.state.inputFocus }
    );

    return (
      <div className={positionStyle}>
        <div className="popover-header">
          <span>{this.props.type}</span>
          <div className="close-icon" onClick={this.props.disableSortSelectMode}><i className="fa fa-times" /></div>
        </div>
        <div className="popover-body">
          <div className="search-bar">
            <div className={searchIconStyle}><i className="fa fa-search" /></div>
            <div className="input-bar">
              <div className="form-group">
                <input
                  className="form-control"
                  value={this.state.query}
                  type="text"
                  onChange={this.onQueryKeyDown}
                  onFocus={this.onInputFocus}
                  onBlur={this.onInputBlur}
                />
              </div>
            </div>
          </div>
          <div className="rows">
            {optionsList}
          </div>
        </div>
      </div>
    );
  }
}));

module.exports = TagFilterPopover;
