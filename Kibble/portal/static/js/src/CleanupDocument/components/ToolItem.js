import { DragSource } from 'react-dnd';
import { PropTypes } from 'prop-types';
import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { ListGroupItem, Label } from 'react-bootstrap';
import { Types } from 'CleanupDocument/redux/constants.js';
import { manageDrop, manageDrag } from 'CleanupDocument/redux/actions.js';

const labelStyle = {
  display: 'inline-block',
  marginRight: 5,
  position: 'relative',
  top: -2,
  background: '#337ab7'
};

const toolSource = {
  beginDrag(props, monitor, component) {
    const item = { tool: props.tool };
    return item;
  },

  endDrag(props, monitor, component) {
      if (!monitor.didDrop()) {
        return;
      }
      props.manageDrag(props.tool);
      const result = monitor.getDropResult();
      props.manageDrop(props.tool, result.selected);
  }
};

class ToolItem extends React.Component {
  render() {
    const { tool, position, isDragging, connectDragSource } = this.props;
    return connectDragSource(
       <div>
        <ListGroupItem>
          {tool.tool}
          <div className="pull-right">
            { isDragging || <Label style={labelStyle}>{position !== -1 ? position : ''}</Label>}
          </div>
        </ListGroupItem>
      </div>
    );
  }
}

ToolItem.propTypes = {
  tool: PropTypes.object.isRequired,
  position: PropTypes.number.isRequired
};

const mapStateToProps = (state) => {
  return { };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    manageDrag, manageDrop
  }, dispatch)
};

ToolItem = DragSource(Types.TOOL, toolSource, (connect, monitor) => ({
  connectDragSource: connect.dragSource(),
  isDragging: monitor.isDragging()
}))(ToolItem);

export default connect(mapStateToProps, mapDispatchToProps)(ToolItem);
