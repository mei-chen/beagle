import React, { PropTypes } from 'react';

const ShortUrl = ({ url, className }) => {
  return (
    <span
      title={url}
      className={className || ''}>
      { url ? url.replace(/^http[s]?:\/\/[^\/]*/, '') : '' }
    </span>
  )
};

ShortUrl.propTypes = {
  url: PropTypes.string.isRequired,
  className: PropTypes.string
};

export default ShortUrl;
