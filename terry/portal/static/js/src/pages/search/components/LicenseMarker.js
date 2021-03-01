import React, { PropTypes } from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

const LicenseMarker = ({ type }) => {
  const className = type === 'error' ? 'marker marker--error' : 'marker marker--not-specified',
        tooltipText = type === 'error' ? 'Fetch error' : 'Not found',
        tooltip = <Tooltip id="tooltip">{tooltipText}</Tooltip>

  return (
    <OverlayTrigger placement="bottom" overlay={tooltip}>
      <i className={`fa fa-circle ${className}`}></i>
    </OverlayTrigger>
  )
};

LicenseMarker.propTypes = {
  type: PropTypes.oneOf(['error', 'not-specified']).isRequired
};

export default LicenseMarker;
