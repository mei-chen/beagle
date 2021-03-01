var React = require('react');
var Spinkit = require('react-spinkit');
var classNames = require('classnames');

require('./styles/Spinner.scss')


var Spinner = React.createClass({

  render() {
    var style;
    if (this.props.inline) {
      style = 'inline';
    } else if (this.props.center) {
      style = 'center';
    } else {
      style = 'widget-size';
    }

    const spinnerClasses = classNames(
      'beagle-spinner',
      style
    );

    return (
      <div className={spinnerClasses}>
        <Spinkit spinnerName="rotating-plane" />
      </div>
    );
  }

});

module.exports = Spinner;
