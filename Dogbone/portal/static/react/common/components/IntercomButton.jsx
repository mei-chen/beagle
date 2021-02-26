import React from 'react';

const IntercomButton = () => {
  return (
    <div
      className="intercom-button"
      title="Contact Us"
      onClick={() => window.Intercom('show')}>
      <span className="fa fa-comments" />
    </div>
  )
};

export default IntercomButton;
