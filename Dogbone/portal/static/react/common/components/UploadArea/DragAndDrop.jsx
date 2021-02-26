/* NPM Modules */
import React from 'react';
import classNames from 'classnames';

require('./styles/Dropzone.scss');

const DropZone = React.createClass({

  getInitialState() {
    return {
      isActive : false
    };
  },

  /* onDrop(e)
  *
  * transfer the onDrop event up to the given onLocalFileDrop
  * prop function
  */
  onDrop(e) {
    e.preventDefault();
    this.setState({ isActive: false });
    this.props.onLocalFileDrop(e);
  },

  /* onDragOver(e)
  *
  * ensure that the dropeffect while dragging over is
  * 'copy'
  */
  onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  },


  /* onDragLeave(e)
  *
  * toggle off the absolutely placed dropzone overlay when the user has a
  * dragged element
  */
  onDragLeave(e) {
    e.preventDefault();
    this.setState({ isActive : false });
  },

  render() {
    const dropZoneClass = classNames(
      'dropzone',
      { 'active' : this.state.isActive }
    );

    //this css class causes the children of the dropzone to ignore mouse triggers
    //unfortunately it needs to be added here and not in the scss because 'React'
    var disableStyle = { 'pointer-events': 'none' };

    return (
      <div className={dropZoneClass} onDrop={this.onDrop} onDragOver={this.onDragOver} onDragLeave={this.onDragLeave}>
        <div className="drop-area" style={disableStyle}>
          <div className="drop-area-text" style={disableStyle}>Drop Document Here</div>
        </div>
      </div>
    );
  }

});

var DragAndDrop = React.createClass({

  propTypes: {
    onLocalFileDrop: React.PropTypes.func
  },

  render() {
    return (
      <div className="option drag-and-drop">
        <DropZone ref="Dropzone" onLocalFileDrop={this.props.onLocalFileDrop}/>
        <i className="fa fa-plus-circle fa-4x" />
        <div className="local-upload-text">
          <span>Drag and Drop a file</span>
        </div>
      </div>
    );
  }
});

module.exports = DragAndDrop;
