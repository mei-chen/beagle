import React, { PropTypes } from 'react';

const IMAGES = {
  defaultImg: '/static/img/logo.svg',
  whiteImg: '/static/img/logo-white.svg',
  defaultTxt: '/static/img/logo-text.svg',
  whiteTxt: '/static/img/logo-text-white.svg'
}

const Logo = ({ white, className }) => {
  return (
    <a href="/" className={className || ''}>
      <img
        className="logo-image"
        src={white ? IMAGES.whiteImg : IMAGES.defaultImg}
        alt="Terry"/>
      <img
        src={white ? IMAGES.whiteTxt : IMAGES.defaultTxt}
        alt="Terry"/>
    </a>
  );
};

Logo.propTypes = {
  white: PropTypes.bool,
  className: PropTypes.string
}

export default Logo;
