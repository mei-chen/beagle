import React from 'react';
import 'base/scss/misc.scss';

// Spinner
const Spinner = ({ message, style }) => (
  <div className="spinner" style={style}>
    <div className="double-bounce1"></div>
    <div className="double-bounce2"></div>
    {message && <div className="message">{message}</div>}
  </div>
);


const LoadAnimation = () =>
  <div className="spin-loader-wrapper">
    <div className="spin-loader"></div>
  </div>;


export { LoadAnimation, Spinner };
