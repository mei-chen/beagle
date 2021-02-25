import React from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

const InCollaborationIcon = () => {
  return (
    <OverlayTrigger placement="top" overlay={ <Tooltip id="collaboration-tooltip">In collaboration</Tooltip> }>
      <i className="collaborator-icon fa fa-portrait" />
    </OverlayTrigger>
  )
};

export default InCollaborationIcon;
