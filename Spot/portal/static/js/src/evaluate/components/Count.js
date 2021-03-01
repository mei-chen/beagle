import React, { PropTypes } from 'react';

const Count = ({ total, positive, negative }) => {
  return (
    <div className="dataset-preview-count">
      <span>{ total } rows </span>
      { !!(positive || negative) && (
        <span>
          (
          <span className="text-success">{ positive }</span> /
          <span className="text-danger"> { negative }</span>
          )
        </span>
      ) }
    </div>
  )
};

Count.propTypes = {
  total: PropTypes.number.isRequired,
  positive: PropTypes.number,
  negative: PropTypes.number
};

export default Count;
