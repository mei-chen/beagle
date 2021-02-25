import React, { PropTypes } from 'react';
import { ButtonGroup, Button } from 'react-bootstrap';

const StatusButtons = ({ onSetLabel, onSetBody }) => {
  return (
    <ButtonGroup className="status-buttons">
      <Button
        onClick={onSetBody}>
        <i className="fa fa-align-left"/> Body
      </Button>
      <Button
        onClick={onSetLabel}>
        <i className="fa fa-tag"/> Labels
      </Button>
    </ButtonGroup>
  )
}

StatusButtons.propTypes = {
  onSetLabel: PropTypes.func.isRequired,
  onSetBody: PropTypes.func.isRequired
}

export default StatusButtons;
