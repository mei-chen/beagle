import React, { Component, PropTypes } from 'react';
import { FormControl } from 'react-bootstrap';
import enhanceWithClickOutside from 'react-click-outside';

class EditableText extends Component {
  constructor(props) {
    super(props);
    this._handleInputChange = this._handleInputChange.bind(this);
    this._startEditing = this._startEditing.bind(this);
    this._endEditing = this._endEditing.bind(this);
    this._save = this._save.bind(this);
    this._renderIcons = this._renderIcons.bind(this);
    this._mounted = null;
    this.state = {
      isEdit: false,
      value: props.text,
      isSaving: false
    }
  }

  componentDidMount() {
    this._mounted = true;
  }

  componentWillReceiveProps(nextProps) {
    if(this.props.text !== nextProps.text) this.setState({ value: nextProps.text });
  }

  componentWillUnmount() {
    this._endEditing();
    this._mounted = false;
  }

  handleClickOutside() {
    this.setState({ isEdit: false, value: this.props.text })
  }

  _handleInputChange(e) {
    this.setState({ value: e.target.value })
  }

  _startEditing() {
    this.setState({ isEdit: true })
  }

  _endEditing() {
    this.props.onCancel && this.props.onCancel();
    this.setState({ isEdit: false, isSaving: false, value: this.props.text })
  }

  _save() {
    const { onSave, asyncSave } = this.props;
    const { value } = this.state;

    if(asyncSave) {
      this.setState({ isSaving: true });
      onSave(value)
        // prevent updating state on unmounted component
        .then(res => this._mounted && this._endEditing())
        .catch(err => this._mounted && this.setState({ isSaving: false }))

    } else {
      onSave(value);
      this._endEditing();
    }
  }

  _renderIcons(isEdit, isSaving) {
    if(isEdit) {
      return isSaving ? (
        <i className="editable-icon editable-icon--spinner fa fa-spinner fa-spin fa-fw" />
      ) : (
        <span>
          <i
            className="editable-icon editable-icon--save fa fa-check text-success"
            onClick={ this._save } />
          <i
            className="editable-icon editable-icon--cancel fa fa-times"
            onClick={ this._endEditing } />
        </span>
      )
    } else {
      return (
        <i
          className="editable-icon editable-icon--edit fa fa-edit"
          onClick={ this._startEditing } />
      )
    }
  }

  render() {
    const { text, onSave, className, inputType } = this.props;
    const { isEdit, value, isSaving } = this.state;

    return(
      <div className={className ? `editable ${className}` : 'editable'}>

        { isEdit ? (
          <FormControl
            className="editable-input"
            value={ value }
            onChange={ this._handleInputChange }
            componentClass={inputType || 'input'}
          />
        ) : (
          <span className="editable-value">{ text }</span>
        )}

        <span className="editable-icons">
          { this._renderIcons(isEdit, isSaving) }
        </span>
      </div>
    )
  }
}

EditableText.propTypes = {
  text: PropTypes.string.isRequired,
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func,
  className: PropTypes.string,
  asyncSave: PropTypes.bool,
  inputType: PropTypes.oneOf(['input', 'textarea'])
};

export default enhanceWithClickOutside(EditableText);
