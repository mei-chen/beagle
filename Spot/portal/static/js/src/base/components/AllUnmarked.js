import React, { PropTypes } from 'react';

const AllUnmarked = ({ onPosClick, onNegClick }) => {
  return (
    <div className="label-item label-item--all">
      <span className="label-item-title">All unmarked</span>
      <span className="label-item-buttons">
        <i
          className="fa fa-check-circle"
          onClick={onPosClick} />
        <i
          className="fa fa-minus-circle"
          onClick={onNegClick} />
      </span>
    </div>
  )
};

AllUnmarked.propTypes = {
  onPosClick: PropTypes.func.isRequired,
  onNegClick: PropTypes.func.isRequired
};

export default AllUnmarked;
