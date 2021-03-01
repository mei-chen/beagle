/*
 * thanks for nothing (yikes)
 * https://github.com/paramaggarwal/react-dropzone
 * nah I'm just playin', couldn't have done this
 * without your code, dude
 */

import React from 'react';
import ReactDOM from 'react-dom';

require('./styles/Dropzone.scss');


const Dropzone = React.createClass({
  propTypes: {
    onDrop: React.PropTypes.func.isRequired,
    size: React.PropTypes.number,
    style: React.PropTypes.object,
    enabled: React.PropTypes.bool,
  },

  getInitialState() {
    return {
      isDragActive: false
    };
  },

  onDragLeave() {
    this.setState({
      isDragActive: false
    });
  },

  onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';

    this.setState({
      isDragActive: true
    });
  },

  onDrop(e) {
    e.preventDefault();

    this.setState({
      isDragActive: false
    });

    //Don't allow file drops after sniff
    if (this.props.enabled) {
      var fileList;
      if (e.dataTransfer) {
        fileList = e.dataTransfer.files;
      } else if (e.target) {
        fileList = e.target.files;
      }

      if (this.props.onDrop) {
        this.props.onDrop(fileList);
      }
    }
  },

  onClick() {
    //Don't launch filepicker if sniff has already been clicked
    if (this.props.enabled) {
      ReactDOM.findDOMNode(this.refs.fileInput).click();
    }
  },

  render() {
    let className = 'dropzone';
    if (this.state.isDragActive) {
      className += ' active';
    }

    let style = this.props.style || {
      width: this.props.size || 100,
      height: this.props.size || 100,
      borderStyle: this.state.isDragActive ? 'solid' : 'dashed'
    };

    if (this.props.className) {
      style = this.props.style;
    }

    return (
      <div className={className} style={style} onClick={this.onClick} onDragLeave={this.onDragLeave} onDragOver={this.onDragOver} onDrop={this.onDrop}>
        <input style={{ display: 'none' }} type="file" ref="fileInput" onChange={this.onDrop} multiple/>
        {this.props.children}
      </div>
    );
  }

});

module.exports = Dropzone;
