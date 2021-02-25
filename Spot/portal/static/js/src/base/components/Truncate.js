import React, { PropTypes } from 'react';

const Truncate = ({ children, maxLength }) => {
  return children.length > maxLength ? (
    <span title={ children }>{ children.substring(0, maxLength) + '...' }</span>
  ) : (
    <span>{ children }</span>
  );
};

Truncate.PropTypes = {
  children: PropTypes.string.isRequired,
  maxLength: PropTypes.number.isRequired
};

export default Truncate;
