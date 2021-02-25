import React, { PropTypes } from 'react';

const Progress = ({ value, fade }) => {
  const percent = Math.round(value * 100) + '%';

  return (
    <span className="prog">
      <span className="prog-bar">
        <span 
          className="prog-bar-fill" 
          style={{ width: percent }} />
      </span>
      <span className="prog-value">{percent}</span>
    </span>
  )
};

Progress.propTypes = {
  value: PropTypes.number.isRequired
};

export default Progress;
