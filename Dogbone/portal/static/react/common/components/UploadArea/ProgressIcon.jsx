var React = require('react');
var Spinkit = require('react-spinkit');
require('./styles/ProgressIcon.scss');


var ProgressIcon = React.createClass({

  propTypes: {
    status: React.PropTypes.oneOf([ null, 'started', 'finished']).isRequired,
  },

  render() {
    var icon;
    const status = this.props.status;

    if (status === null) {
      icon = <i className="fa fa-hourglass"></i>;

    } else if (status === 'started') {
      icon = <i className="fa fa-cog fa-spin"></i>;

    } else if (status === 'finished') {
      icon = <i className="fa fa-check" />;
    }

    return (
      <span className="beagle-progress-icon">
        {icon}
      </span>
    );
  }

});


module.exports = ProgressIcon;
