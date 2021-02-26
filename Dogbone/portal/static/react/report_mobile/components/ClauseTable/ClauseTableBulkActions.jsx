/* NPM Modules */
import _ from 'lodash';
var React = require('react');
var Reflux = require('reflux');
var classNames = require('classnames');
var { Typeahead } = require('react-typeahead');
var $ = require('jquery');

/* Utilities */
var validateEmail = require('utils/validateEmail');

/* Bootstrap Requirements */
var Button = require('react-bootstrap/lib/Button');

/* Components */
var BulkTagTools = require('./BulkTagTools');

/* Stores & Actions */
var ReportStore = require('report/stores/ReportStore');
var { ReportActions } = require('report/actions');

/* Style */
require('./styles/ClauseTableBulkActions.scss');

var ClauseTableBulkActions = React.createClass({

  propTypes: {
    sentences: React.PropTypes.array.isRequired,
  },

  getInitialState() {
    return {
      typeaheadOptions : [],
      inputFocus : false,
      showButton : false,
    };
  },

  assignEmail() {
    var email = this.refs.invite.state.entryValue;
    var sentenceIdxs = _.pluck(this.props.sentences, 'idx');
    if (!validateEmail(email)) {
      Notification.error(`${email} is an invalid email`);
      return
    }

    if (this.isExistingCollaborator(email) || this.isDocumentOwner(email)) {
      ReportActions.assignSentences(email, sentenceIdxs);
    } else if (this.isOwner()) {

      var onSuccess = resp => {
        ReportActions.assignSentences(email, sentenceIdxs);
      }
      var onError = resp => {
        log.error('Report::onAdd error', resp);
        Notification.error(email +  ': ' + JSON.parse(resp.responseText).message);
      }
      //first invite the user, then assign them to the sentences
      ReportActions.inviteUser(email, undefined, onSuccess, onError);

    } else {
      Notification.error(`Document owner must first invite ${email} to assign clauses to them`);
    }
    //clear the input
    this.refs.invite.setState({entryValue : ''});
  },

  componentDidMount() {
    $.get('/api/v1/user/me/collaborators')
      .done(resp => {
        var emails = _.map(resp.objects, u => u.email);
        this.setState({ typeaheadOptions: emails });
      })
      .fail(resp => log.error(resp));
  },

  /**
  *handleKeyPress
  *
  *event handler for <enter> key shared user submission
  */
  handleKeyPress(e) {
     if (e.which === 13){   //enter pressed
      this.assignEmail();
     }
  },

  //Returns true is the provided email is the owner's email not to be
  //confused with isOwner() which checks to see if the requesting user
  //also owns the docmument
  isDocumentOwner(email) {
    return ReportStore.isDocumentOwner(email);
  },

  //Returns a boolean if the CURRENT user is also the owner
  isOwner() {
    return ReportStore.isOwner();
  },

  isExistingCollaborator(email) {
    return ReportStore.isExistingCollaborator(email);
  },

  setInputFocus(e) {
    this.setState({
      inputFocus : true,
      showButton : true,
    });
  },

  removeInputFocus(e) {
    var showButton = this.refs.invite.state.entryValue.length > 0;
    this.setState({
      inputFocus : false,
      showButton : showButton
    });
  },

  generateBulkTagTools() {
    const { sentences, user } = this.props;
    return (
      <div className="bulk-tag-tool">
        <span className="bulk-subtitle">Tag Selected</span>
        <BulkTagTools key={sentences.length} sentences={sentences} user={user} />
      </div>
    );
  },

  generateInviteCollaborators() {
    var inputStyle = classNames(
      'search-icon',
      {'active' : this.state.inputFocus},
    );
    //only show the input button if there is some text in the input field
    var submitButton = this.state.showButton > 0 ? <Button bsStyle='success' onClick={this.assignEmail}>Assign</Button> : null;
    return (
      <div className="invite-collaborators">
        <span className="bulk-subtitle">Assign Selected</span>
        <div className="invite-panel">
          <div className="search-container">
            <div className={inputStyle}><i className="fa fa-envelope-o" /></div>
             <Typeahead ref="invite"
              maxVisible={5}
              placeholder="Assign a specified email to selected clauses"
              options={this.state.typeaheadOptions}
              onKeyDown={this.handleKeyPress}
              onFocus={this.setInputFocus}
              onBlur={this.removeInputFocus}
            />
            {submitButton}
          </div>
          <div className='bulk-spacer'></div>
        </div>
      </div>
    ) //value={this.state.query} onChange={this.onQueryKeyDown} onFocus={this.setInputFocus} onBlur={this.removeInputFocus}
  },

  render() {
    var sentences = this.props.sentences;
    var bulkTagTools = this.generateBulkTagTools();
    var inviteCollaborators = this.generateInviteCollaborators();

    return (
      <div className="bulk-actions">
        <span className="bulk-title">Bulk Actions <span className="bulk-title-meta">({sentences.length})</span></span>
        {bulkTagTools}
        {inviteCollaborators}
      </div>
    );
  }

});

module.exports = ClauseTableBulkActions;
