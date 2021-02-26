/* NPM Modules */
import React from 'react';
import classNames from 'classnames';

/* Style */
require('./styles/ClauseTablePagination.scss');

var ClauseTablePagination = React.createClass({

  propTypes: {
    pageCount : React.PropTypes.number.isRequired,
    totalPages : React.PropTypes.number.isRequired,
    incrementPage : React.PropTypes.func.isRequired,
    decrementPage : React.PropTypes.func.isRequired,
    hasPagePrev : React.PropTypes.bool.isRequired,
    hasPageNext : React.PropTypes.bool.isRequired
  },

  onPageIncrementClick() {
    if (this.props.pageCount < this.props.totalPages) {
      this.props.incrementPage();
    }
  },

  onPageDecrementClick() {
    if (this.props.pageCount > 0) {
      this.props.decrementPage();
    }
  },

  render() {
    var pagePrevStyle = classNames(
      'pagination-option',
      { 'enabled' : this.props.hasPagePrev }
    );

    var pageNextStyle = classNames(
      'pagination-option',
      { 'enabled' : this.props.hasPageNext }
    );

    return (
      <div className="pagination">
        <div className={pagePrevStyle}>
            <i className="fa fa-chevron-left" onClick={this.onPageDecrementClick}/>
          </div>
          <span>{this.props.pageCount} of {this.props.totalPages}</span>
        <div className={pageNextStyle}>
            <i className="fa fa-chevron-right" onClick={this.onPageIncrementClick}/>
        </div>
      </div>
    )
  }
});


module.exports = ClauseTablePagination;