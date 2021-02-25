import React, { PropTypes } from 'react';

const SortIcon = ({ columnIndex, sortedColumnIndex, sortedDirection, onClick }) => {
  const classNames = ['sort-icon'];

  if(columnIndex === sortedColumnIndex) {
    classNames.push('active')
    sortedDirection === 'asc' ? classNames.push('asc') : classNames.push('desc');
  }

  return (
    <span
      className={classNames.join(' ')}
      onClick={() => onClick(columnIndex)}></span>
  )
};

SortIcon.propTypes = {
  columnIndex: PropTypes.number.isRequired,
  sortedColumnIndex: PropTypes.number, // could be null
  sortedDirection: PropTypes.oneOf(['asc', 'desc']), // could be null
  onClick: PropTypes.func.isRequired
};

export default SortIcon;
