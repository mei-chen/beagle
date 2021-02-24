import React, { Component, PropTypes } from 'react';

class AddButton extends Component {
  constructor(props) {
    super(props)
    this._toggleOpen = this._toggleOpen.bind(this);
    this._handleItemClick = this._handleItemClick.bind(this);
    this.state = {
        open: false
    }
  }

  _toggleOpen() {
    this.setState({ open: !this.state.open });
  }

  _handleItemClick(type) {
    this.props.onClick(type);
    this.setState({ open: false });
  }

  render() {
    const { open } = this.state;
    const className = open ? 'add add--open' : 'add';
    const sign = open ?
                (<i className="fa fa-caret-left" aria-hidden="true"></i>) :
                (<i className="fa fa-plus" aria-hidden="true"></i>)

    return (
      <div className={className}>
        <span
          className="add-plus"
          onClick={this._toggleOpen}>{sign}</span>

        { open ? (
          <div className="add-list">
            <span
              className="add-item"
              onClick={() => this._handleItemClick('regex')}>
              <i className="add-icon add-icon--regex fa fa-superscript" />
              Regex
            </span>
            <span
              className="add-item"
              onClick={() => this._handleItemClick('builtin')}>
              <i className="add-icon fa fa-archive" />
              BuiltIn Classifier
            </span>
            <span
              className="add-item"
              onClick={() => this._handleItemClick('trained')}>
              <i className="add-icon fa fa-magic" />
              Trained Classifier
            </span>
          </div>
        ) : (
          <span
            className="add-label"
            onClick={this._toggleOpen}>Add</span>
        ) }
      </div>
    )
  }
}

AddButton.propTypes = {
    onClick: PropTypes.func.isRequired
}

export default AddButton;
