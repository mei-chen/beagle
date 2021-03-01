/* NPM Modules */
import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import classNames from 'classnames';
import { Typeahead } from 'react-typeahead';
import $ from 'jquery';

/* Utilities */
import validateEmail from 'utils/validateEmail';
import log from 'utils/logging';
/* Bootstrap Requirements */
import Button from 'react-bootstrap/lib/Button';

/* Components */
import BulkTagTools from './BulkTagTools';

/* Stores & Actions */
import {
  inviteUser,
  assignSentences
} from 'report/redux/modules/report';

/* Style */
require('./styles/ClauseTableBulkActions.scss');

const ClauseTableBulkActions = React.createClass({

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

  componentDidMount() {
    $.get('/api/v1/user/me/collaborators')
      .done(resp => {
        var emails = _.map(resp.objects, u => u.email);
        this.setState({ typeaheadOptions: emails });
      })
      .fail(resp => log.error(resp));
  },

  assignEmail() {
    const email = this.refs.invite.state.entryValue;
    const sentenceIdxs = _.map(this.props.sentences, 'idx');
    const { isOwner, dispatch } = this.props;

    if (!validateEmail(email)) {
      Notification.error(`${email} is an invalid email`);
      return
    }

    if (this.isExistingCollaborator(email) || this.isDocumentOwner(email)) {
      dispatch(assignSentences(email, sentenceIdxs));
    } else if (isOwner) {
      // var onSuccess = () => {
      //   ReportActions.assignSentences(email, sentenceIdxs);
      // }
      // var onError = resp => {
      //   log.error('Report::onAdd error', resp);
      //   Notification.error(email + ': ' + JSON.parse(resp.responseText).message);
      // }
      //first invite the user, then assign them to the sentences
      // ReportActions.inviteUser(email, undefined, onSuccess, onError);
      dispatch(inviteUser(email, undefined))
        .then(() => dispatch(assignSentences(email, sentenceIdxs)));
    } else {
      Notification.error(`Document owner must first invite ${email} to assign clauses to them`);
    }
    //clear the input
    this.refs.invite.setState({ entryValue : '' });
  },


  /**
  *handleKeyPress
  *
  *event handler for <enter> key shared user submission
  */
  handleKeyPress(e) {
    if (e.which === 13) {   //enter pressed
      this.assignEmail();
    }
  },

  //Returns true is the provided email is the owner's email not to be
  //confused with isOwner() which checks to see if the requesting user
  //also owns the docmument
  isDocumentOwner(email) {
    const { report } = this.props;
    return report.get('owner').get('email') === email;
  },

  isExistingCollaborator(email) {
    const { report } = this.props;
    return report.get('collaborators').find(x => x.get('email') === email);
  },

  setInputFocus() {
    this.setState({
      inputFocus : true,
      showButton : true,
    });
  },

  removeInputFocus() {
    var showButton = this.refs.invite.state.entryValue.length > 0;
    this.setState({
      inputFocus : false,
      showButton : showButton
    });
  },

  renderTagsLoading() {
    const { isBulkTagRequesting } = this.props;
    if (isBulkTagRequesting) {
      return (
        <i className="fa fa-spinner fa-pulse active" style={{ marginTop: '2px' }}/>
      )
    }
  },


  generateBulkTagTools() {
    const { sentences, user } = this.props;
    return (
      <div className="bulk-tag-tool">
        <span className="bulk-subtitle">Tag Selected {this.renderTagsLoading()}</span>
        <BulkTagTools key={sentences.length} sentences={sentences} user={user} />
      </div>
    );
  },

  generateInviteCollaborators() {
    var inputStyle = classNames(
      'search-icon',
      { 'active' : this.state.inputFocus },
    );
    //only show the input button if there is some text in the input field
    var submitButton = this.state.showButton > 0 ? <Button bsStyle="success" onClick={this.assignEmail}>Assign</Button> : null;
    return (
      <div className="invite-collaborators">
        <span className="bulk-subtitle">Assign Selected</span>
        <div className="invite-panel">
          <div className="search-container">
            <div className={inputStyle}><i className="fa fa-envelope" /></div>
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
          <div className="bulk-spacer" />
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

const mapStateToProps = (state) => {
  return {
    report: state.report,
    isBulkTagRequesting: state.report.get('isBulkTagRequesting'),
    isOwner: (
      state.report.get('uuid') && // Make sure that report has been fetched
      state.report.get('owner').get('username') == state.user.get('username')
    )
  }
};

export default connect(mapStateToProps)(ClauseTableBulkActions);
