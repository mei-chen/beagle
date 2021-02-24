import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import {
  ListGroup,
  ListGroupItem,
  Grid,
  Col,
  Button,
  Glyphicon,
  OverlayTrigger,
  Tooltip
} from 'react-bootstrap';
import DebounceInput from 'react-debounce-input';

import "../scss/FileController.scss"

import { setFileToBatch } from 'BatchManagement/redux/actions';
import { MODULE_NAME } from 'BatchManagement/constants';
import { filterObjects } from 'base/utils/misc';
import uuid from 'uuid';

const FileListItem = ({ item, handleClick, isBound }) => {
  const onClick = () => handleClick(item.resource_uri);
  const tooltip = (id) =>
    <Tooltip id={id}>
        Click to {(isBound) ? "remove" : "add"} file
    </Tooltip>;

  return (
    <ListGroupItem>
      <div className="file-wraper">
        <div title={item.filename} className="file-title">{item.filename}</div>
        <OverlayTrigger
          trigger={['hover']}
          placement="top"
          overlay={tooltip(`tooltip-${item.id}`)}
        >
          <Button bsSize="xsmall" onClick={onClick}>
            <Glyphicon glyph={(isBound) ? "remove" : "plus"}/>
          </Button>
        </OverlayTrigger>
      </div>
    </ListGroupItem>
  );
};


class FileController extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      searchTerm: ''
    };
    this.search = (ev) => {
      this.setState({ searchTerm: ev.target.value })
    };
    this.getFiltered = () => {
      return filterObjects(this.props.unboundFiles, 'filename', this.state.searchTerm);
    };
    this.bind = (uri) => {
      this.props.setFileToBatch(uri, this.props.batch);
    };
    this.unbind = (uri) => {
      this.props.setFileToBatch(uri, undefined);
    };
  }

  renderListOfFiles(list, isBound, handler) {
    return list.map((item) => (
      <FileListItem
        item={item}
        isBound={isBound}
        handleClick={handler}
        key={uuid.v4()}
      />
    ));
  }

  render() {
    const { boundFiles } = this.props;
    return (
      <Grid>
        <Col xs={6} md={6}>
          <ListGroup className="scrollable filelist-left">
            {this.renderListOfFiles(boundFiles, true, this.unbind)}
          </ListGroup>
        </Col>
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
          <ListGroup className="scrollable filelist-right">
            {this.renderListOfFiles(this.getFiltered(), false, this.bind)}
          </ListGroup>
        </Col>
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    boundFiles: state[ MODULE_NAME ].get('boundFiles'),
    unboundFiles: state[ MODULE_NAME ].get('unboundFiles')
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    setFileToBatch
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(FileController);
