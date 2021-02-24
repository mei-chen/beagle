import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import ToolList from 'CleanupDocument/components/ToolList';

import { getCleanupDocTools } from 'base/redux/modules/tools';

import { MODULE_NAME } from 'CleanupDocument/constants'

class CleanupToolsController extends React.Component {
  componentWillMount() {
    // Load tools
    this.props.getCleanupDocTools();
  }
  render() {
    const { tools, toolsState, toolsCount } = this.props;
    return (
      <Grid>
        <Col xs={12} md={12}>
          <ToolList list={tools} maxcount={toolsCount} selected={false}/>
          <ToolList list={toolsState} maxcount={toolsCount} selected={true}/>
        </Col>
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    tools: state[ MODULE_NAME ].get('tools'),
    toolsState: state[ MODULE_NAME ].get('toolsState'),
    toolsCount: state[ MODULE_NAME ].get('toolsCount'),
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getCleanupDocTools
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(CleanupToolsController);
