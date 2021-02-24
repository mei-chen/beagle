import React from 'react';
import { findDOMNode } from 'react-dom'
import { DragSource, DropTarget, DragDropContext } from 'react-dnd'
import HTML5Backend from 'react-dnd-html5-backend'

const ItemTypes = {
  TOOL: 'tool',
}

const toolSource = {
  beginDrag(props) {
    return {
      id: props.id,
      index: props.index,
    }
  },

  endDrag(props, monitor) {
    props.apllyOnDrop();
  }
}

const toolTarget = {
  hover(props, monitor, component) {
    const dragIndex = monitor.getItem().index
    const hoverIndex = props.index

    // Don't replace items with themselves
    if (dragIndex === hoverIndex) {
      return
    }

    // Determine rectangle on screen
    const hoverBoundingRect = findDOMNode(component).getBoundingClientRect()

    // Get vertical middle
    const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2

    // Determine mouse position
    const clientOffset = monitor.getClientOffset()

    // Get pixels to the top
    const hoverClientY = clientOffset.y - hoverBoundingRect.top

    // Only perform the move when the mouse has crossed half of the items height
    // When dragging downwards, only move when the cursor is below 50%
    // When dragging upwards, only move when the cursor is above 50%

    // Dragging downwards
    if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
      return
    }

    // Dragging upwards
    if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
      return
    }

    // Time to actually perform the action
    props.moveTool(dragIndex, hoverIndex)

    // Note: we're mutating the monitor item here!
    // Generally it's better to avoid mutations,
    // but it's good here for the sake of performance
    // to avoid expensive index searches.
    monitor.getItem().index = hoverIndex
  },
}

class ToolComponent extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      tool,
      isDragging,
      connectDragSource,
      connectDropTarget,
    } = this.props
    const opacity = isDragging ? 0 : 1

    return connectDragSource(
      connectDropTarget(
        <div style={{ opacity }}
          className="tool selected"
        >
          {tool.tool_name}
          <div className="indicator selected" onClick={() => this.props.handleClickOnTool(tool)}>
            <i className="far fa-times" aria-hidden="true"/>
          </div>
        </div>
      ),
    )
  }
}

const Tool =  DragSource(ItemTypes.TOOL, toolSource, (connect, monitor) => ({
  connectDragSource: connect.dragSource(),
  isDragging: monitor.isDragging(),
}))(
DropTarget(ItemTypes.TOOL, toolTarget, connect => ({
  connectDropTarget: connect.dropTarget(),
}))(ToolComponent))


class DNDToolsComponent extends React.Component {
  render() {
    const { changeSetting, auto_cleanup_tools, handleClickOnTool, moveTool, apllyOnDrop } = this.props;

    return(
      <span>
        {auto_cleanup_tools.map((tool,key) => 
          <Tool
            key={tool.id}
            index={key}
            id={tool.id}
            tool={tool}
            changeSetting={changeSetting}
            handleClickOnTool={handleClickOnTool}
            moveTool={moveTool}
            apllyOnDrop={apllyOnDrop}
          /> 
        )}          
      </span>
    )
  }
}

export const DNDTools = DragDropContext(HTML5Backend)(DNDToolsComponent)
