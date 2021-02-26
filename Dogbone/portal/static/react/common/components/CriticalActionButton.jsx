import React from 'react';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import classNames from 'classnames';

/* Component Stylings */
require('./styles/CriticalActionButton.scss');


const CriticalActionButton = React.createClass({

  propTypes: {
    title: React.PropTypes.oneOfType([
      React.PropTypes.object,
      React.PropTypes.string,
    ]),
    id: React.PropTypes.string,
    styleClass:React.PropTypes.string,
    // Button's initial mode:
    //   {'active', 'confirmation', 'inactive'}
    mode: React.PropTypes.string,
    action: React.PropTypes.func,
    tooltipMessage: React.PropTypes.string,
  },

  getInitialState() {
    return {
      mode: this.props.mode,
    }
  },

  goToConfirmation() {
    this.setState({ mode: 'confirmation' });
  },

  goToInactive() {
    this.setState({ mode: 'inactive' });
  },

  goToActive() {
    this.setState({ mode: 'active' });
  },

  doAction() {
    this.props.action();
    this.goToInactive();
  },

  render() {
    var spanClass = classNames('critical-action-' + this.state.mode,this.props.styleClass);

    var btn;
    if (this.state.mode == 'active') {
      btn = (
        <span className={spanClass} onClick={this.goToConfirmation}>
          {this.props.title}
        </span>
      );
    } else if (this.state.mode == 'inactive') {
      btn = (
        <span className={spanClass}>
          {this.props.title}
        </span>
      );
    } else if (this.state.mode == 'confirmation') {
      btn = (
        <span className={spanClass}>
          <span onClick={this.doAction} className="approve"><i className="fa fa-check" /></span>
          <span onClick={this.goToActive} className="reject">Cancel</span>
        </span>
      );
    }

    var wrapped_btn = btn;
    if (this.props.tooltipMessage) {
      let overlaymsg = (<Tooltip id={this.props.id || this.props.title}>{this.props.tooltipMessage}</Tooltip>);
      wrapped_btn = (
        <OverlayTrigger placement="left" overlay={overlaymsg}>
          {btn}
        </OverlayTrigger>
      );
    }

    return wrapped_btn;
  }
});

module.exports = CriticalActionButton;
