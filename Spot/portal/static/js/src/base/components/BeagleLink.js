import React from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

const BeagleLink = () => {
  return (
    <OverlayTrigger placement="left" overlay={<Tooltip id="beagle-tooltip">Grant access to the Spot API for your Beagle account</Tooltip>}>
      <a
        className="beagle-link"
        href="/api/v1/dogbone/authorize/">
        <img src="static/img/beagle-logo.png" width="25px" />
        Connect to Beagle
      </a>
    </OverlayTrigger>
  )
};

export default BeagleLink;
