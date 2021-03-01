import React from 'react';
import { Col, Row, ListGroup, PageHeader, small } from 'react-bootstrap';
import { DropTarget } from 'react-dnd';
import { Types } from 'CleanupDocument/redux/constants.js';
import ToolItem from 'CleanupDocument/components/ToolItem.js';

const toolListTarget = {
  canDrop(props, monitor) {
      return true;
  },

  drop(props, monitor, component) {
    if (monitor.didDrop()) {
      return;
    }
    return { selected: props.selected };
  }
};

class ToolList extends React.Component {
  renderToolList() {
      const { list, selected } = this.props;
      return list.map((tool, index) => (
        <ToolItem
          key={`key_${index}_${tool.tool.split(' ').join('-')}`}
          tool={tool}
          position={selected ? index : -1}
        />
      ));
  };

  needHint() {
      const { maxcount, list } = this.props;
      return list.size < maxcount;
  }

  renderHint() {
    return (
     <Col  xs={12} md={12} className="droparea">
       <h2 className="text-center"><small>Drop tools here</small></h2>
     </Col>
    )
  }

  render() {
    const { connectDropTarget,  } = this.props;
    return connectDropTarget(
      <div>
        <Col xs={6} md={6}>
          <ListGroup>
            {this.renderToolList()}
            {this.needHint() ? this.renderHint() : null}
          </ListGroup>          
        </Col>
      </div>
    );
  }
}

ToolList = DropTarget(Types.TOOL, toolListTarget, (connect, monitor) => ({
  // Call this function inside render()
  // to let React DnD handle the drag events:
  connectDropTarget: connect.dropTarget(),
  // You can ask the monitor about the current drag state:
  isOver: monitor.isOver(),
  isOverCurrent: monitor.isOver({ shallow: true }),
  canDrop: monitor.canDrop(),
  itemType: monitor.getItemType()
}))(ToolList);
export default ToolList;
