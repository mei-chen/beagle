/* NPM Modules */
var React = require('react');
var Reflux = require('reflux');
var classNames = require('classnames');

/* Components */
var EditorBox = require('../EditorBox');

/* Style */
require('./styles/ClauseBody.scss');


var Clause = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
  },

  disableEditMode: function() {
  },

  render() {
    return (
      <EditorBox
        noCloseBtn
        sentence={this.props.sentence}
        disableEditMode={this.disableEditMode}
      />
    );
  }

});


var ClauseBody = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object,
    user: React.PropTypes.object.isRequired,
  },

  getSentence() {
    var sentence = this.props.sentence;
    if (sentence) {
      return (
        <Clause
          key={sentence.idx}
          sentence={sentence}
          user={this.props.user}
        />
      );
    }
    else {
      return (
        <div className="no-clause">
          <span>Sorry, there is no unreviewed clause.</span>
        </div>
      );
    }
  },

  render() {
    var clause = this.getSentence();
    return (
      <div className="clause-body">
        {clause}
      </div>
    );
  }
});

module.exports = ClauseBody;
