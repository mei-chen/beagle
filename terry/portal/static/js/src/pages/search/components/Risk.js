import React, { PropTypes } from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

const map = {
  high: {
    value: 70,
    color: '#de7c65'
  },
  middle: {
    value: 40,
    color: 'orange'
  },
  low: {
    value: 6,
    color: '#f3e079'
  },
  extralow: {
    value: 0,
    color: '#add2be'
  }
}

const getColor = value => {
  if(value >= map.high.value) {
    return map.high.color;
  } else if(value >= map.middle.value) {
    return map.middle.color;
  } else if(value >= map.low.value) {
    return map.low.color;
  } else if(value >= map.extralow.value) {
    return map.extralow.color;
  }
}

const Risk = ({ value }) => {
  if(value === null) return <i className="no-risk-data fa fa-times" />;

  const tooltip = <Tooltip id="tooltip">Risk is { value + '%' }</Tooltip>;

  return (
    <OverlayTrigger placement="top" overlay={tooltip}>
      <i className={'fa fa-circle marker'} style={{ color: getColor(value) }} />
    </OverlayTrigger>
  )
};

Risk.propTypes = {
  value: PropTypes.number // could be null
};

export default Risk;
