import React from 'react';
import PropTypes from 'prop-types';
import { DragDropContext } from 'react-dnd';
import HTML5Backend from 'react-dnd-html5-backend';

class Root extends React.Component {
  render() {
    return this.props.children;
  }
}

Root.propTypes = {
  children: PropTypes.element,
};

export default DragDropContext(HTML5Backend)(Root);
