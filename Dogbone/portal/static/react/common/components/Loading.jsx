import React, { Component } from 'react';

export default class Root extends Component {
  render() {
    return (
      <div className="container">
        <div className="row">
            <div className="center-block">
              <div className="loading">
                <i className="fa fa-cog fa-spin fa-3x" />
                <div className="loading-text" />
              </div>
            </div>
        </div>
      </div>
    )
  }
}
