import React from 'react';

const IntercomButton = () => {
  return(
    <div
      className="intercom-button"
      title="Contact Us"
      onClick={() => window.Intercom('show')}>
		  <span className="fal fa-comments"></span>
	  </div>
  )
};

export default IntercomButton;
