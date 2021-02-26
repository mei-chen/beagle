var React = require('react');
var classNames = require('classnames');
var OnClickOutside = require('react-onclickoutside');

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

    var icon = this.props.option.icon ? <i className={this.props.option.icon}/> : null;

    return (
      <div className="row" onClick={this.onSelectOption}>
        <div className="check">
          <i className={checkStyle}/>
        </div>
        <div className="option-name">
          <span className={optionStyle}>{this.props.option.display}</span>
          {icon}
        </div>
      </div>
    );
  }
});

var TagFilterPopover = React.createClass({

  propTypes: {
    disableSortSelectMode: React.PropTypes.func.isRequired,
    options: React.PropTypes.array.isRequired,
    type: React.PropTypes.string.isRequired,
    onSelectOption: React.PropTypes.func.isRequired,
  },

  mixins: [OnClickOutside],

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
      return <PopoverOption option={o} onSelectOption={this.onSelectOption}/>;
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
          <div className="close-icon" onClick={this.props.disableSortSelectMode}><i className="fa fa-close" /></div>
        </div>
        <div className="popover-body">
          <div className="search-bar">
            <div className={searchIconStyle}><i className="fa fa-search" /></div>
            <div className="input-bar">
              <input value={this.state.query} type="text" onChange={this.onQueryKeyDown} onFocus={this.onInputFocus} onBlur={this.onInputBlur}/>
            </div>
          </div>
          <div className="rows">
            {optionsList}
          </div>
        </div>
      </div>
    );
  }
});

module.exports = TagFilterPopover;
