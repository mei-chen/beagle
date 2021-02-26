/* NPM Modules */
var React = require('react');

/* Style */
require('./styles/LocalFile.scss');

var LocalFile = React.createClass({

  propTypes: {
    onLocalClick: React.PropTypes.func
  },

  /**
  * onLocalClick()
  *
  * Onclick listener that will artifically click the hidden form input
  * via a prop method.
  */
  onLocalClick() {
    this.props.onLocalClick();
  },

  render() {
    return (
      <div className="option local" onClick={this.onLocalClick}>
        <i className="fa fa-desktop fa-4x" />
        <div className="local-upload-text">
          <span>Upload from your computer</span>
        </div>
      </div>
    );
  }

});


module.exports = LocalFile;