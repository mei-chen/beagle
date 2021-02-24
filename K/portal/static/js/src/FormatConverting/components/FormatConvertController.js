import React from 'react';
import PropTypes from 'prop-types';
import ImmutablePropTypes from 'react-immutable-proptypes';
import { List } from 'immutable';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import {
  ListGroup,
  ListGroupItem,
  Grid,
  Col,
  Button,
  Glyphicon,
  Panel
} from 'react-bootstrap';
import DebounceInput from 'react-debounce-input';
import { updateFilter, setState } from 'FormatConverting/redux/actions';
import { postConvert } from 'base/redux/modules/conversion';
import { MODULE_NAME } from 'FormatConverting/constants';
import { SwitchSelectState } from 'base/components/DefaultButtons';


class FileListItem extends React.Component {
  constructor(props) {
    super(props);
    this.check = () => {
      const { setState, file, state } = this.props;
      setState(file.id, !state);
    }
  }

  render() {
    const { file, state } = this.props;
    return (
      <ListGroupItem onClick={this.check}>
        <div className="pull-right">
          {
            state === true ? <Glyphicon glyph="check"/>
              : <Glyphicon glyph="unchecked"/>
          }
        </div>
        <div className="nonconverted-list">
          {file.filename} {file.need_ocr ? "(requires OCR)" : ""}
        </div>
      </ListGroupItem>
    );
  }
}

FileListItem.propTypes = {
  file: PropTypes.object.isRequired,
  state: PropTypes.bool.isRequired,
  setState: PropTypes.func.isRequired
};

class TxtFileListItem extends React.Component {
    renderLinkIcon(doc) {
        if (doc.content_file || doc.text_file) {
            return (
                <span className="glyphicon glyphicon-download-alt"></span>
            );
        }
        return null;
    }
    renderLink(text, url) {
        if (url) {
            return (
                <a className="ml-3" href={url}>{text}</a>
            );
        }
        return null;
    }
    render() {
        const { doc } = this.props;
        return (
          <ListGroupItem>
            <div className="pull-right">
              {this.renderLinkIcon(doc)}
              {this.renderLink('txt', doc.text_file)}
              {this.renderLink('docx', doc.content_file)}
            </div>
            <div className="converted-list">{doc.name}</div>
          </ListGroupItem>);
    };
}

TxtFileListItem.propTypes = {
  doc: PropTypes.object.isRequired,
};

class FormatConvertController extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedFile: null,
      searchTerm: '',
    };

    this.fileChange = file => this.setState({ selectedFile: file });
    this.filterChange = ev => this.setState({
      searchTerm: ev.target.value.toLowerCase()
    });
    this.getFilteredFiles = this.getFilteredFiles.bind(this);
    this.switchSelectedState = this.switchSelectedState.bind(this);
    this.doConvert = this.doConvert.bind(this);

  }

  getFilteredFiles() {
    const { files } = this.props;
    const { searchTerm } = this.state;
    return files.filter((item) => {
      return (!searchTerm) || item.content.toLowerCase().indexOf(searchTerm) !== -1;
    });
  }

  switchSelectedState(state = true) {
    const files = this.getFilteredFiles();
    for (const file of files) {
      this.props.setState(file.id, state)
    }
  }

  doConvert() {
    const { fileState, postConvert } = this.props;
    const selectedFiles = Object.keys(fileState).filter((item) => {
      return (fileState[ item ] === true);
    });
    if (selectedFiles.length) {
      postConvert(selectedFiles);
    }
  }

  renderListOfFiles() {
    const { selectedFile } = this.state;
    const { fileState, setState } = this.props;
    const files = this.getFilteredFiles();
    return files.map((file) => (
      <FileListItem
        key={file.id}
        file={file}
        active={file.id === selectedFile}
        setState={setState}
        state={fileState[file.id] === true}
        handleSelect={this.fileChange}
      />
    ));
  }

  renderTxtProcessedListOfFiles() {
    const { docs } = this.props;
    return docs.map((doc) => (
      <TxtFileListItem
        key={doc.id}
        doc={doc}
      />
    ));
  }

  downloadUri(batchId, plain) {
    let uri = window.CONFIG.API_URLS.batchDownload + '?batch=' + batchId;
    if (plain) {
      uri += '&plaintext=1';
    }
    return uri;
  }

  render() {
    const filesListGroup = (
      <div className="project-list-selector">
        <ListGroup className="scrollable list-files-left">
          {this.renderListOfFiles()}
        </ListGroup>
      </div>
    );
    const processedTxtFilesListGroup = (
      <div className="project-list-selector">
        <ListGroup className="scrollable list-files-right">
          {this.renderTxtProcessedListOfFiles()}
        </ListGroup>
      </div>
    );
    const downloadButtons = (
      <Panel>
        <a href={this.downloadUri(this.props.batch.id, false)}>
          <Button>
            <span className="glyphicon glyphicon-download-alt mr-3"></span>
            All docx
          </Button>
        </a>
        <a href={this.downloadUri(this.props.batch.id, true)}>
          <Button>
            <span className="glyphicon glyphicon-download-alt mr-3"></span>
            All txt
          </Button>
        </a>
      </Panel>
    );

    return (
      <Grid>
        <Col xs={6} md={6}>
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
            onSelectAll={() => this.switchSelectedState(true)}
            onDeselectAll={() => this.switchSelectedState(false)}
          />
          {filesListGroup}
          <Panel>
            <Button onClick={this.doConvert}>Convert</Button>
          </Panel>
        </Col>
        <Col xs={6} md={6}>
          {processedTxtFilesListGroup}
          {this.props.docs.length && downloadButtons}
        </Col>
      </Grid>
    );
  }
}


FileListItem.propTypes = {
  files: PropTypes.object,
  state: PropTypes.bool.isRequired,
  setState: PropTypes.func.isRequired
};
TxtFileListItem.propTypes = {
  filenum: PropTypes.number,
};
FormatConvertController.propTypes = {
  files: ImmutablePropTypes.list.isRequired,
  docs: ImmutablePropTypes.list.isRequired
};
FormatConvertController.defaultProps = {
  files: new List(),
  docs: new List(),
  fileState: {}
};


const mapStateToProps = (state) => {
  return {
    files: state[ MODULE_NAME ].batch_files,
    docs: state[ MODULE_NAME ].batch_docs,
    fileState: state[ MODULE_NAME ].fileState,
    fileFilterValue: state[ MODULE_NAME ].fileFilterValue
  };
};
const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    updateFilter, setState, postConvert
  }, dispatch)
}
export default connect(mapStateToProps, mapDispatchToProps)(FormatConvertController);
