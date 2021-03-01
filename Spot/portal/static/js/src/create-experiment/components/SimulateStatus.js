import React, { PropTypes } from 'react';
import { Label } from 'react-bootstrap';

const SimulateStatus = ({ status }) => {
  const text = status ? 'True' : 'False';
  const bsStyle = status ? 'success' : 'default';
  return <Label className="simulate-status" bsStyle={bsStyle}>{ text }</Label>
};

SimulateStatus.propTypes = {
  status: PropTypes.bool.isRequired
};

export default SimulateStatus;
