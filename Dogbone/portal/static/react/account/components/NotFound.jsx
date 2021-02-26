import React from 'react';

// App
import css from './styles/NotFound.css';

export default React.createClass({
  render() {
    return (
      <div className={css.notFoundPage}>
        <h1>We are sorry!</h1>
        The path
        <span className={css.badPath}>{this.props.location.pathname}</span>
        is invalid. Click on any of the navigation buttons on the left to view
        your agreement.
      </div>
    );
  }
});
