/* NPM Modules */
var React = require('react');
var Reflux = require('reflux');
var classNames = require('classnames');

/* Style */
require('./styles/Pagination.scss');

var Pagination = React.createClass({

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
      <div className='pagination'>
        <div className='pagination-pages'>
          <p>{this.props.pageCount} of {this.props.totalPages}</p>
        </div>
        <div className='pagination-buttons'>
          <div className={pagePrevStyle}>
              <i className='fa fa-chevron-left' onClick={this.onPageDecrementClick}/>
            </div>
          <div className={pageNextStyle}>
              <i className='fa fa-chevron-right' onClick={this.onPageIncrementClick}/>
          </div>
        </div>
      </div>
    )
  }
});


module.exports = Pagination;
