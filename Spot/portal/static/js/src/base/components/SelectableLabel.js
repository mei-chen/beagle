import React, { Component, PropTypes } from 'react';
import { FormControl, MenuItem } from 'react-bootstrap';
import Dropdown from 'react-bootstrap/lib/Dropdown';
import { List } from 'immutable';

class SelectableLabel extends Component {
  constructor(props) {
    super(props);
    this._endEditing = this._endEditing.bind(this);
    this._save = this._save.bind(this);
    this._mounted = null;
    this.state = {
      isSaving: false
    }
  }

  componentDidMount() {
    this._mounted = true;
  }

  componentWillUnmount() {
    this._mounted = false;
  }

  _endEditing() {
    this.setState({ isSaving: false })
  }

  _save(option) {
    const { onSave, asyncSave } = this.props;

    if(asyncSave) {
      this.setState({ isSaving: true });
      onSave(option)
        // prevent updating state on unmounted component
        .then(res => this._mounted && this._endEditing())
        .catch(err => this._mounted && this._endEditing())

    } else {
      onSave(option);
      this.setState({ isSaving: false })
    }
  }

  _renderOptions(options) {
    return options.map((option, i) => (
      <MenuItem 
        key={i}
        onClick={() => this._save(option)}>{ option === '' ? <i className="empty-value-icon fa fa-circle" title="Empty label" /> : option }</MenuItem>
    ))
  }

  render() {
    const { label, options } = this.props;
    const { isSaving } = this.state;

    return(
      <div className="selectable">
        { label === '' ? <i className="empty-value-icon fa fa-circle" title="Empty label" /> : label }
        <Dropdown id="labels">
          { isSaving && <i className="selectable-icon selectable-icon--spinner fa fa-spinner fa-spin fa-fw" /> }
          <CustomToggle bsRole="toggle" style={{ display: isSaving ? 'none' : 'inline-block' }} />
          <Dropdown.Menu className="selectable-drop">
            { this._renderOptions(options) }
          </Dropdown.Menu>
        </Dropdown>
      </div>
    )
  }
}

const CustomToggle = ({ children, onClick, style }) => {
  return <i style={style} className="selectable-icon selectable-icon--edit fa fa-edit" onClick={ (e) => onClick(e) }>{ children }</i>
}

SelectableLabel.propTypes = {
  label: PropTypes.string.isRequired,
  options: PropTypes.instanceOf(List),
  asyncSave: PropTypes.bool
};

export default SelectableLabel;
