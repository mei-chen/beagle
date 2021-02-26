import React from 'react';
import Spinkit from 'react-spinkit';
require('./styles/ProgressIcon.scss');


const ProgressIcon = React.createClass({
  propTypes: {
    status: React.PropTypes.oneOf([ null, 'started', 'finished']),
  },

  render() {
    let icon;
    const status = this.props.status;

    if (status === null) {
      icon = null;
    } else if (status === 'started') {
      icon = <Spinkit spinnerName="circle" noFadeIn />;
    } else if (status === 'finished') {
      icon = <i className="fa fa-check" />;
    }

    return (
      <div className="beagle-progress-icon">
        {icon}
      </div>
    );
  }

});


module.exports = ProgressIcon;
