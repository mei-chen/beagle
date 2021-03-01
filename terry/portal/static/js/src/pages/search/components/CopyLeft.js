import React, { PropTypes } from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

const CopyLeft = ({ value }) => {
  if(!value) return null;

  const tooltip = <Tooltip id="tooltip">License considered to be Copyleft</Tooltip>;

  return (
    <OverlayTrigger placement="bottom" overlay={tooltip}>
      <i className="fa fa-circle marker marker--copyleft" />
    </OverlayTrigger>
  )
};

CopyLeft.propTypes = {
  value: PropTypes.bool.isRequired
};

export default CopyLeft;
