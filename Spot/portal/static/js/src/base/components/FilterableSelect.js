import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';
import { DropdownButton, MenuItem, FormControl } from 'react-bootstrap';

class FilterableSelect extends Component {
  constructor(props) {
    super(props);
    this._filterItems = this._filterItems.bind(this);
    this._handleInputChange = this._handleInputChange.bind(this);
    this._renderItems = this._renderItems.bind(this);
    this._handleDropToggle = this._handleDropToggle.bind(this);
    this._chooseItem = this._chooseItem.bind(this);

    const { chosenByDefault, getter } = this.props;

    this.state = {
      chosenTitle: chosenByDefault ? getter(chosenByDefault) : '',
      query: '',
      dropdownOpen: false
    }
  }

  componentDidMount() {
    const { chosenByDefault } = this.props;
    if(chosenByDefault) this._chooseItem(chosenByDefault);
  }

  _filterItems(items, query) {
    const { getter } = this.props;
    return items.filter(item => getter(item).toLowerCase().indexOf(query) !== -1);
  }

  _handleInputChange(e) {
    this.setState({ query: e.target.value.toLowerCase() })
  }

  _renderItems(items) {
    const { getter, renderer } = this.props;
    return items.map((item, i) => (
      <MenuItem
        key={i}
        className="filterable-search-result"
        onClick={() => { this._chooseItem(item) } }>
        { renderer ? renderer(item) : getter(item) }
      </MenuItem>
    ))
  }

  _handleDropToggle(isOpen, e, data) {
    // prevent drop from closing on input click
    if(e.target.closest('.filterable-search-result') === null && data.source === 'select') {
      return false;
    }
    this.setState({ dropdownOpen: isOpen })
  }

  _chooseItem(item) {
    const { onClick, getter } = this.props;

    this.setState({ chosenTitle: getter(item) });
    onClick && onClick(item);
  }

  render() {
    const { chosenTitle, dropdownOpen, query } = this.state;
    const { items, placeholder } = this.props;

    return (
      <DropdownButton
        title={ chosenTitle ||  placeholder || 'Select an item' }
        id="filterable-select"
        open={ dropdownOpen }
        onToggle={ this._handleDropToggle } >
        <MenuItem className="filterable-search">
          <FormControl
            value={ query }
            onChange={this._handleInputChange} />
        </MenuItem>
        { this._renderItems( this._filterItems(items, query) ) }
      </DropdownButton>
    )
  }
}

FilterableSelect.propTypes = {
  onClick: PropTypes.func.isRequired,
  getter: PropTypes.func.isRequired,
  renderer: PropTypes.func.isRequired,
  items: PropTypes.instanceOf(List).isRequired,
  chosenByDefault: PropTypes.any,
  placeholder: PropTypes.string
}

export default FilterableSelect;
