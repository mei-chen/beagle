import React, { PropTypes } from 'react';

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

const Score = ({ value }) => {
  return (
    <span className="score" style={{ backgroundColor: getColor(value) }}>{ value + '%' }</span>
  )
};

Score.propTypes = {
  value: PropTypes.number
};

export default Score;
