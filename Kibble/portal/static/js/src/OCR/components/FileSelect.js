import React, { Component } from "react";
import PropTypes from 'prop-types';
import { connect } from "react-redux";
import {
  ListGroup,
  ListGroupItem,
  Col,
  Glyphicon,
} from "react-bootstrap";
import DebounceInput from "react-debounce-input";
import { SwitchSelectState } from 'base/components/DefaultButtons';
import ProcessedFileList from 'OCR/components/ProcessedFileList';
import { LoadAnimation } from 'base/components/misc'


class FileListItem extends React.Component {
  constructor(props) {
    super(props);
    this.check = () => this.props.updateFileIds(this.props.fileId);

  }

  renderCheckBox() {
    if (this.props.disabled) {
      return <LoadAnimation />
    }
    return <Glyphicon glyph={this.props.checked ? 'check' : 'unchecked'}/>
  }

  render() {
    return (
      <ListGroupItem onClick={!this.props.disabled ? this.check : () => ({})} disabled={this.props.disabled}>
        {this.props.fname}
        <div className="pull-right">
          {this.renderCheckBox()}
        </div>
      </ListGroupItem>
    );
  }
}
FileListItem.propTypes = {
  fileId: PropTypes.number.isRequired,
  fname: PropTypes.string.isRequired,
  updateFileIds: PropTypes.func.isRequired
};


class FileSelect extends Component {
  constructor(props) {
    super(props);
    this.state = {
      searchTerm: ''
    };

    this.filterChange = (ev) => {
      this.setState({ searchTerm: ev.target.value.toLowerCase() })
    };

    this.getFilteredFiles = this.getFilteredFiles.bind(this);
    this.selectAll = this.selectAll.bind(this);
  }

  getFilteredFiles() {
    const { searchTerm } = this.state;
    return this.props.ocrStore.get('unprocessedFiles').filter((file) => {
      return !searchTerm || file.filename.toLowerCase().indexOf(searchTerm) !== -1
    })
  }

  selectAll(switchTo) {
    if (!switchTo) {
      this.props.updateFileIds();
      return;
    }
    const processingFiles = this.props.ocrStore.get('processingFiles')
    this.props.updateFileIds(
      this.getFilteredFiles()
        .filter(file => !processingFiles.includes(file.id))
        .map(file => file.id)
    )
  }

  renderUnprocessedFileList() {
    const files = this.getFilteredFiles();
    return files.map(file =>
      <FileListItem
        key={file.id}
        fname={file.filename}
        fileId={file.id}
        updateFileIds={this.props.updateFileIds}
        checked={this.props.isFileSelected(file.id) === true}
        disabled={this.props.ocrStore.get('processingFiles').includes(file.id) === true}
      />
    )
  }

  render() {
    return (
      <div>
        <Col xs={6} md={6}>
          <strong>Need OCR</strong>
          <DebounceInput
            type="text"
            className="search-projects"
            name="search-projects"
            placeholder="Search"
            minLength={2}
            debounceTimeout={100}
            onChange={this.filterChange}
          />
          <SwitchSelectState
            onSelectAll={() => this.selectAll(true)}
            onDeselectAll={() => this.selectAll(false)}
          />
          <ListGroup className="file-list">
            {this.renderUnprocessedFileList()}
          </ListGroup>

        </Col>

        <Col xs={6} md={6}>
          <strong>Already Processed</strong>
          <ProcessedFileList />
        </Col>
      </div>
    )
  }
}

export default connect(
  (state) => ({
    ocrStore: state.ocrStore
  })
)(FileSelect)
