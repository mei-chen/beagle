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
import { filterObjects } from 'base/utils/misc';
import { addBatchProject, delBatchProject } from 'ProjectManagement/redux/actions';
import { MODULE_NAME } from 'ProjectManagement/constants';
import 'ProjectManagement/scss/BatchController.scss';


class BatchItem extends React.Component {
  constructor(props) {
    super(props);
    this.onClick = () => this.props.handleClick(this.props.item.resource_uri);
  }

  tooltip(id, bound) {
    const action = (bound) ? "remove" : "add";
    return (
      <Tooltip id={id}>
        Click to {action} batch
      </Tooltip>
    );
  };

  render() {
    const { item, isBound } = this.props;
    const glyph = (isBound) ? "remove" : "plus";
    return (
      <ListGroupItem>
        {item.name}
        <OverlayTrigger
          trigger={['hover']}
          placement="top"
          overlay={this.tooltip(`tooltip-${item.id}`, isBound)}
        >
          <Button className="pull-right" bsSize="xsmall"
                  onClick={this.onClick}>
            <Glyphicon glyph={glyph}/>
          </Button>
        </OverlayTrigger>
      </ListGroupItem>
    );
  }
}


class BatchController extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      searchTerm: ''
    };

    this.handleSearch = (ev) => this.setState({ searchTerm: ev.target.value });
    this.bindBatch = (uri) => this.props.addBatchProject(uri, this.props.project);
    this.unbindBatch = (uri) => this.props.delBatchProject(uri, this.props.project);
  }

  getFilteredBatches() {
    return filterObjects(this.props.unboundBatches, 'name', this.state.searchTerm);
  }

  renderListOfBatches(list, isBound, handler) {
    return list.map((item) => (
      <BatchItem
        item={item}
        key={item.id}
        isBound={isBound}
        handleClick={handler}
      />
    ));
  }

  render() {
    const { boundBatches } = this.props;
    return (
      <Grid>
        <Col xs={6} md={6}>
          <ListGroup>
            {this.renderListOfBatches(boundBatches, true, this.unbindBatch)}
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
            onChange={this.handleSearch}
          />
          <ListGroup>
            {this.renderListOfBatches(this.getFilteredBatches(), false, this.bindBatch)}
          </ListGroup>
        </Col>
      </Grid>
    );
  }
}


const mapStateToProps = (state) => {
  return {
    boundBatches: state[ MODULE_NAME ].get('boundBatches'),
    unboundBatches: state[ MODULE_NAME ].get('unboundBatches'),
    batchFilterValue: state[ MODULE_NAME ].get('batchFilterValue')
  };
};


const mapDispatchToProps = dispatch => bindActionCreators({
  addBatchProject, delBatchProject
}, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(BatchController);
