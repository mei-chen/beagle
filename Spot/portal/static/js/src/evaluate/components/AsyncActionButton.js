import React, { PropTypes } from 'react';
import { Button } from 'react-bootstrap';

const AsyncActionButton = ({ children, isWaiting, waitingText, onClick, disabled }) => {
  return (
    <Button 
      onClick={ onClick }
      bsStyle="primary"
      disabled={ isWaiting }
    >
      { isWaiting ? (
        <span>
          <i className="fa fa-spinner fa-pulse fa-fw" /> 
          {` ${waitingText}`}
        </span>
      ) : (
        <span>{ children }</span>
      ) }
    </Button>
  )
};

AsyncActionButton.propTypes = {
  children: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).isRequired,
  isWaiting: PropTypes.bool.isRequired,
  waitingText: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
}

export default AsyncActionButton;
