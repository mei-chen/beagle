import React from 'react';
import PropTypes from 'prop-types';
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
import { SwitchSelectState } from 'base/components/DefaultButtons';


class FileListItem extends React.Component {
  render() {
    const { filenum } = this.props;

    return (
      <ListGroupItem
        onClick={this.props.handleClick}>
        file#{filenum}.docx
        <div className="pull-right">
          {
            this.props.active ? <Glyphicon glyph="check"/> :
              <Glyphicon glyph="unchecked"/>
          }
        </div>
      </ListGroupItem>
    );
  }
}

FileListItem.propTypes = {
  filenum: PropTypes.number,
};

class TxtFileListItem extends React.Component {
  render() {
    const { filenum } = this.props;
    return (
      <ListGroupItem>
        converted_file{filenum}.txt
      </ListGroupItem>);
  };
}

TxtFileListItem.propTypes = {
  filenum: PropTypes.number,
};

class CleanupSentencesController extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      files: [
        { resource_uri: 1, selected: false },
        { resource_uri: 1, selected: false },
        { resource_uri: 1, selected: false }
      ]
    };

    this.search = ev => console.log(ev.target.value);

    this.switchSelectedState = this.switchSelectedState.bind(this);
    this.handleClick = this.handleClick.bind(this);

  }

  switchSelectedState(state = true) {
    const files_ = this.state.files;
    files_.map((fileObj) => {
      fileObj.selected = state
    });
    this.setState({ files: files_ })
  };

  handleClick(file, i) {
    const files_ = this.state.files;
    files_[ i ].selected = !files_[ i ].selected;
    this.setState({ files: files_ })
  }

  renderListOfFiles() {
    return this.state.files.map((file, i) => (
      <FileListItem
        key={i}
        filenum={file.resource_uri}
        active={file.selected}
        handleClick={() => this.handleClick(file, i)}
      />
    ));
  }

  renderTxtProcessedListOfFiles() {
    return [ 1, 2, 3, 4, 5 ].map((v, k) => (
      <TxtFileListItem
        key={k}
        filenum={v}
      />
    ));
  }

  render() {
    const filesListGroup = (
      <div className="project-list-selector">
        <ListGroup>
          {this.renderListOfFiles()}
        </ListGroup>
      </div>
    );
    const processedTxtFilesListGroup = (
      <div className="project-list-selector">
        <ListGroup>
          {this.renderTxtProcessedListOfFiles()}
        </ListGroup>
      </div>
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
            onChange={this.search}
          />
          <SwitchSelectState
            onSelectAll={() => this.switchSelectedState(true)}
            onDeselectAll={() => this.switchSelectedState(false)}
          />
          {filesListGroup}
          <Panel>
            <Button>Process</Button>
          </Panel>
        </Col>
        <Col xs={6} md={6}>
          {processedTxtFilesListGroup}
        </Col>
      </Grid>
    );
  }
}

CleanupSentencesController.propTypes = {};

export default CleanupSentencesController;
