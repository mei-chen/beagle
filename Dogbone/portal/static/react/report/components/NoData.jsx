var React = require('react');
require('./styles/NoData.scss');


var NoData = React.createClass({

  render() {
    return (
      <div className="no-data-container">
        <span className="no-data-content">
          No data found
        </span>
      </div>
    );
  }

});

var NoDataContextV = React.createClass({

  render() {
    var msg = 'No data found';
    if (this.props.info) {
      msg = (
        <span>
          <i className="fa fa-info" />
          {'\u00A0\u00A0\u00A0'}
          {this.props.info}
        </span>
      );
    }
    return (
      <span className="no-data-contextv">
        {msg}
      </span>
    );
  }

});


module.exports = {
  NoData: NoData,
  NoDataContextV: NoDataContextV
};
