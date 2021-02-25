import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';
import chroma from 'chroma-js';

const COLORS = {
  low: '#e74c3c',
  high: '#2ecc71'
}

class AccordMatrix extends Component {
  constructor(props) {
    super(props);
    this._renderUser = this._renderUser.bind(this);
    this._renderMatrix = this._renderMatrix.bind(this);
    this._renderCell = this._renderCell.bind(this);
    this.scale = chroma.scale([COLORS.low, COLORS.high]);
  }

  _renderUser(user) {
    return (
      <div
        className="accord-user">
        <i className="fa fa-user" />{ user }
      </div>
    )
  }

  _renderCell(i, values, user) {
    if(values === null) {
      return (
        <div
          key={i}
          className="accord-cell accord-cell--no-data" />
      )
    };



    return (
      <OverlayTrigger
        key={i}
        placement="top"
        overlay={<Tooltip id="accord-user-tooltip">{ user } - { Math.round(values.get(1) * 100) + '%' }</Tooltip>}>
        <div
          className="accord-cell"
          style={{
            opacity: values.get(0),
            backgroundColor: this.scale(values.get(1)).hex()
          }}/>
      </OverlayTrigger>
    )
  }

  _renderMatrix(matrix, users) {
    return matrix.map((row, rowI) => (
      <div
        key={rowI}
        className="accord-row clearfix">
        { this._renderUser(users.get(rowI)) }
        { row.map((values, columnI) => this._renderCell(columnI, values, users.get(columnI))) }
      </div>
    ))
  }

  render() {
    const { users, matrix } = this.props;

    return (
      <div className="accord">
        { this._renderMatrix(matrix, users) }
      </div>
    )
  }
}

AccordMatrix.propTypes = {
  users: PropTypes.instanceOf(List).isRequired,
  matrix: PropTypes.instanceOf(List).isRequired
};

export default AccordMatrix;
