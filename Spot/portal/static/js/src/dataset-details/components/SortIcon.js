import React, { PropTypes } from 'react';

const SortIcon = ({ order, onClick }) => {

  const inactiveStyle = { color: 'rgb(204, 204, 204)', margin: '0' }

  if(order) {
    return (
      <span className="order">
        { order === 'asc' ? (
          <span className="dropup"><span className="caret"></span></span>
        ) : (
          <span className="dropdown"><span className="caret"></span></span>
        ) }
      </span>
    )
  }

  return (
    <span className="order">
      <span className="dropdown"><span className="caret" style={inactiveStyle}></span></span>
      <span className="dropup"><span className="caret" style={inactiveStyle}></span></span>
    </span>
  )
};

SortIcon.propTypes = {
  order: PropTypes.oneOf(['asc', 'desc'])
}

export default SortIcon;