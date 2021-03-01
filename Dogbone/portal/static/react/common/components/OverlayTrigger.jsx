var React = require('react');
var Tooltip = require('react-bootstrap/lib/Tooltip');

require('./styles/OverlayTrigger.scss');   //stylings for component

var OverlayTrigger = React.createClass({

  getInitialState() {
    return {
      hover : false, 
    };
  },

  propTypes: {
      placement: React.PropTypes.string.isRequired,
      overlay: React.PropTypes.element.isRequired
  },


  onMouseOver() {
    this.setState({ hover : true });
  },

  onMouseLeave() {
    this.setState({ hover : false });
  },

  render() {
    var tooltip = this.state.hover ? this.props.overlay : null;

    return (
      <div className="overlay-trigger" onMouseOver={this.onMouseLeave} onMouseLeave={this.onMouseOver}>
        {this.props.children}
        {tooltip}
      </div>
    );
  }

});

module.exports = OverlayTrigger;