import React, { PropTypes } from 'react';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

const InfoIcon = ({ messagesMap }) => {

  const _getMessage = (messagesMap) => {
    if(typeof(messagesMap) === "string"){
      return messagesMap
    }
    for(let message in messagesMap) {
      if(messagesMap[message]) return message;
    }
  };

  const tooltip = <Tooltip id="useful_columns">{ _getMessage(messagesMap) }</Tooltip>

  return (
    <OverlayTrigger overlay={tooltip}>
      <i className="info-icon fa fa-info-circle" />
    </OverlayTrigger>
  )
}

InfoIcon.propTypes = {
   messagesMap: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object
  ]),
}

export default InfoIcon;
