import React, { PropTypes } from 'react'

const Reset = ({ title, onReset }) => {
  return (
    <div className="reset">
      {title}
      <i 
        className="reset-icon fa fa-times"
        onClick={onReset} />
    </div>
  )
}

Reset.propTypes = {
  title: PropTypes.string.isRequired,
  onReset: PropTypes.func.isRequired
}

export default Reset;
