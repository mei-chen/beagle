import React, { Component, PropTypes } from 'react';

class DroppableSection extends Component {
  constructor(props) {
    super(props);
    this._toggleDrop = this._toggleDrop.bind(this);
    this.state = {
      isOpen: true
    }
  }

  _toggleDrop() {
    this.setState({ isOpen: !this.state.isOpen })
  }

  render() {
    const { isOpen } = this.state;
    const { title, children } = this.props;

    return (
      <div className="dataset-preview">
        <h3
          className="dataset-preview-title">
          <span
            className="dataset-preview-title-inner"
            onClick={this._toggleDrop}>
            { title }
            { isOpen ? <i className="fa fa-chevron-up" /> : <i className="fa fa-chevron-down" /> }
          </span>
        </h3>
        { isOpen && (
          <div className="dataset-preview-drop">
            { children }
          </div>
        ) }
      </div>
    )
  }
}

DroppableSection.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.oneOfType([PropTypes.object, PropTypes.array]).isRequired
}

export default DroppableSection;
