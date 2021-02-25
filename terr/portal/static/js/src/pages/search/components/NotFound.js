import React, { PropTypes } from 'react';
import { Link } from 'react-router';

const NotFound = ({ url }) => {
  return(
    <div className="not-found">
      <div className="not-found-message">Couldn't access: { url }</div>
      <div className="not-found-parts">
        <div className="not-found-part">
          <span className="not-found-num">1.</span>
          <div className="not-found-text">Check for typos. It's easier to just paste the repo URL from the browser</div>
        </div>
        <div className="not-found-part">
          <span className="not-found-num">2.</span>
          <div className="not-found-text">If the repo is <span className="not-found-em"><i className="fa fa-lock" />Private</span>, make sure you granted Terry access in <Link to="/settings" className="not-found-em"><i className="fa fa-cog" />Settings</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

NotFound.propTypes = {
  url: PropTypes.string.isRequired
};

export default NotFound;
