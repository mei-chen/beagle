import _ from 'lodash';
import React from 'react';
import $ from 'jquery';
import Timestamp from 'react-time';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import classNames from 'classnames';
import Button from 'react-bootstrap/lib/Button';
import { MentionsInput, Mention } from 'react-mentions';
import Popover from 'react-bootstrap/lib/Popover';
import { connect } from 'react-redux';

import log from 'utils/logging';
import { Notification } from 'common/redux/modules/transientnotification';
import userDisplayName from 'utils/userDisplayName';
import {
  getComments,
  submitComment,
  inviteUser,
  deleteCommentOnServer
} from 'report/redux/modules/report';
import uuidV4 from 'uuid/v4';

const COMMENTS_PER_PAGE = 5;
const COMMENTS_ON_INIT = 5;

const ICONS = {
  wiki_response: 'fa-wikipedia',
  blacks_definition: 'fa fa-bold'
};
const TITLES = {
  wiki_response: 'Wikipedia',
  blacks_definition: 'Black\'s Law Dictionary'
}

require('./styles/CommentPanel.scss');


const MoreComments = React.createClass({

  propTypes: {
    onMore: React.PropTypes.func.isRequired,
    hasAnyComments: React.PropTypes.bool.isRequired,
    hasMoreComments: React.PropTypes.bool
  },

  renderMoreContent() {
    const { hasMoreComments } = this.props;
    if (hasMoreComments) {
      return <span className="more-button" onClick={this.props.onMore}>...</span>
    } else if (hasMoreComments === false) {
      return <span className="no-more">No more comments.</span>
    } else {
      return <span />
    }
  },

  render() {
    if (!this.props.hasAnyComments) {
      return null;
    }

    return (
      <div className="more-comments">
        { this.renderMoreContent() }
      </div>
    );
  }

});

const BotContents = React.createClass({

  propTypes: {
    comment: React.PropTypes.object.isRequired
  },

  render() {
    let { response_type } = this.props.comment;
    let success = !(response_type === 'error');
    let title = this.props.comment.response.title;
    let body = this.props.comment.response.body;
    let icon = success ? ICONS[response_type] : 'fa fa-exclamation';
    let iconTitle = success ? TITLES[response_type] : '';

    let excerptClass = success ? 'excerpt' : 'excerpt-error';
    return (
      <div className={excerptClass}>
        <div className="excerpt-header">
          <span>{title}</span>
          <i className={icon} title={iconTitle} />
        </div>
        <div className="excerpt-body">
          <span>{body}</span>
        </div>
      </div>
    );
  }

});

const UserDetailsPopoverContents = React.createClass({

  propTypes: {
    username: React.PropTypes.string.isRequired
  },

  getInitialState() {
    return {
      user: null
    };
  },

  componentDidMount() {
    this.getPopoverContent();
  },


  componentWillUnmount() {
    if (this.state.user && this.state.user.id !== 'beagle') {
      this.req.abort();
    }
  },

  getPopoverContent() {
    let username = this.props.username;
    //if the user is not 'beagle'
    if (username !== 'beagle') {
      const url = `/api/v1/user/${username}`;
      this.req = $.get(url)
        .done(response => {
          this.setState({ user: response });
        }).fail(response => {
          if (response.statusText !== 'abort') {
            this.setState({ user: response.status });
          }
        });
    }
  },

  generatePopoverContents() {
    var user = this.state.user;

    var avatarStyle, userDetails;
    if (this.props.username !== 'beagle') {
      avatarStyle = { backgroundImage: `url('${user.avatar}')` };
      userDetails = (
        <div className="user-details-text">
          <span className="full-name">{user.first_name} {user.last_name}</span>
          <span className="email">{user.email}</span>
          <span className="last-seen">Last seen&nbsp;
            <Timestamp
              value={user.last_login}
              locale="en"
              titleFormat="YYYY/MM/DD HH:mm"
              relative
            />
          </span>
        </div>
      );
    } else {
      avatarStyle = { backgroundImage: 'url(\'/static/img/Beagle-Logo-120x120.png\')' };
      userDetails = (
        <div className="user-details-text">
          <span className="full-name">Beagle Bot</span>
          <span className="beaglebot-tagline">Your most loyal legal companion.</span>
        </div>
      );
    }

    return (
      <div className="user-details-popover">
        <div className="user-details-avatar">
           <div className="details-avatar" style={avatarStyle}/>
        </div>
        {userDetails}
      </div>
    );
  },

  render() {
    var popOverSpinnerClasses = classNames('fa fa-spinner fa-spin','spinner-margin');
    var spinner = (
      <div className = "spinner-wrapper">
        <i className={popOverSpinnerClasses}/>
      </div>
    );
    var contents = spinner;

    var user = this.state.user;

    if (user === 404) {
      contents = (
        <div>
          <div className="user-details-popover">
            <span className="pending-message">Invitation Pending</span>
          </div>
          {spinner}
        </div>
      );
    }
    //render the user details popover
    else if (user || this.props.username === 'beagle') {
      contents = (
        <div>
          {this.generatePopoverContents()}
          {spinner}
        </div>
      );
    }

    return contents;
  }
});


const Comment = React.createClass({

  propTypes: {
    comment: React.PropTypes.object.isRequired,
    user: React.PropTypes.object.isRequired,
    onDelete: React.PropTypes.func.isRequired
  },

  /*
  * formatMessage(str)
  *
  * creates an array of span elements, @mentions and the runs of text in
  * between them. @mentions are given an Overlay trigger and distingushing
  * className
  */
  formatMessage(str) {
    //Regex pulls out tokens of form '@[username](first lastname)' and '@[user@domain.com](user@domain.com)'
    const activeReg = /@\[[a-zA-Z0-9áàâäãåçéèêëíìîïñóòôöõúùûüýÿæœÁÀÂÄÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸÆŒ\-\+_@.]+\]\([a-zA-Z0-9áàâäãåçéèêëíìîïñóòôöõúùûüýÿæœÁÀÂÄÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸÆŒ\s\-\+_@.,']+\)/g;

    //Regex pulls out tokens of form '@[user@domain.com](user@domain.com)'
    //const pendingReg = /@\[[\w\-_]+[@][\w\-_]+[.][\w\-_]+\]\([\s\w\-_@.]+\)/g;

    //Regex to pull the token surrounded in parentheses
    const displayReg = /\([a-zA-Z0-9áàâäãåçéèêëíìîïñóòôöõúùûüýÿæœÁÀÂÄÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸÆŒ\s\-\+_@.,']+\)/g;

    //regex to pull the token surrounded in square brackets
    const idReg = /\[([a-zA-Z0-9áàâäãåçéèêëíìîïñóòôöõúùûüýÿæœÁÀÂÄÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸÆŒ\s\-\+_@.,']+)\]/g;

    let result = [];
    //build array of mentions
    let matches = str.match(activeReg) || [];

    //build array of fullnames
    let userDisplayTokens = (matches || []).map(m => m.match(displayReg)[0].replace('(', '').replace(')', ''));

    //build an array of usernames
    let userIDTokens = (matches || []).map(m => m.match(idReg)[0].replace('[', '').replace(']', ''));

    //build array of surrounding sentence runs
    let notMatches = str.split(activeReg);

    let key = 0;
    //splice off first element of each array (notMatches will always be 1 element longer than matches)
    while (userDisplayTokens && userDisplayTokens.length > 0) {
      //regular runs with no mentions formatted as spans
      result.push(<span key={key++}>{notMatches.splice(0, 1)[0]}</span>);
      //@ mentions handled as overlay triggers & spans
      let idText = userIDTokens.splice(0, 1)[0];
      let displayText = userDisplayTokens.splice(0, 1)[0];
      //show the '@' sign for existing users, none for emails
      let userRender = (idText.indexOf('@') > -1) ? displayText : ('@' + displayText);
      let popover = <Popover id={uuidV4()} className="popover-dimenssions"><UserDetailsPopoverContents username={idText} /></Popover>;
      result.push(
        <OverlayTrigger id={uuidV4()} key={key++} placement="bottom" overlay={popover}>
          <span className="mention">
            {userRender}
          </span>
        </OverlayTrigger>
      );
    }
    //push last remaining notMatches token onto result
    result.push(<span key={key++}>{notMatches.pop()}</span>);
    return result;
  },

  render() {
    let comment = this.props.comment;
    let user = this.props.user;
    let author = this.props.comment.author;
    let isOwner = user.id === author.id;
    let isImported = this.props.comment.is_imported;
    let originalAuthor = this.props.comment.original_author;
    //TODO: Henry Make use of the response type when deciding if bot response
    let isBot = comment.author.username === '@beagle';

    let name = isBot ? 'Beagle Bot' : userDisplayName(author);

    let avatarURL = isBot ? 'url(\'/static/img/Beagle-Logo-120x120.png\')' : `url('${author.avatar}')`;
    let date = comment.timestamp * 1000;
    //let isOwner = (user.username === author.username);
    let typeClassname = isBot ? 'bot' : 'reg';
    let importedClassname = isImported ? 'imported' : null;
    let bubbleStyle = classNames(
      'bubble', typeClassname, importedClassname
    );
    let headerStyle = classNames(
      'header', typeClassname, importedClassname
    );
    let nameStyle = classNames(
      'name', typeClassname
    );
    let dateStyle = classNames(
      'date', typeClassname
    );
    let contents = isBot ?
      <BotContents comment={this.props.comment}/> :
      <span>{this.formatMessage(comment.message)}</span>;
    let originalAuthorBlock = isImported ? (
      <span className="original-author-wrapper">
        <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Imported</Tooltip>}>
          <i className="fa fa-address-book" />
        </OverlayTrigger>
        <span className="original-author-descr">Original author:</span>
        <span className="original-author-name">{originalAuthor}</span>
      </span>
    ) : null;

    return (
      <div className="comment">
        <div className="avatar" style={{ backgroundImage: avatarURL }} />
        <div className="text">
          <div className={bubbleStyle}>
            <div className={headerStyle}>
              <span className={nameStyle}>{name}</span>
              <span className={dateStyle}>
                <Timestamp
                  value={date}
                  titleFormat="YYYY/MM/DD HH:mm"
                  locale="en"
                  relative
                />
              </span>
              {originalAuthorBlock}
              { isOwner && (
                <i
                  className="delete-icon fa fa-times"
                  onClick={() => this.props.onDelete(comment.uuid)} />
              ) }
            </div>
            <div className="body">
              {contents}
            </div>
          </div>
        </div>
      </div>
    );
  }

});


const NewCommentComponent = React.createClass({

  propTypes: {
    user: React.PropTypes.object.isRequired,
    sentenceIdx: React.PropTypes.number.isRequired,
    onChange: React.PropTypes.func
  },

  getInitialState() {
    return {
      comment: '',
      users: null,
      inviteUserMode: false,
      mentionDescriptor: null,
      querySequenceStart: null,
      querySequenceEnd: null,
      processAddMention: null,
      mentionedUsers: [],
    };
  },

  //TODO: The state has to be set as part of the .done callback, hence why it's done twice.
  // The ajax request should probably be handled in the user store.
  componentDidMount() {
    this.getCommentContent();
  },

  // when comment box content changes run parent onChange function if any
  componentDidUpdate(prevProp, prevState) {
    if (prevState.comment !== this.state.comment && this.props.onChange) {
      this.props.onChange(this.state.comment);
    }
  },

  getCommentContent() {
    const beagle = {
      id: 'beagle',
      display: 'BeagleBot',
      avatar: '/static/img/Beagle-Logo-120x120.png',
      email: ''
    };

    const { isOwner } = this.props;

    //owners get a list of all their old collaborators
    if (isOwner) {
      $.get('/api/v1/user/me/collaborators')
        .done(resp => {
          let users = resp.objects.map(u => {
            return {
              id: u.username,
              display: userDisplayName(u),
              avatar: u.avatar,
              email: u.email
            };
          });
          //add beaglebot too!
          users.push(beagle);
          this.setState({ users: users });
        })
        .fail(resp => log.error(resp));
    }
    //Shared users get a list of everyone collaborating on the document (owner included)
    else {
      const { collaborators } = this.props;
      const users = collaborators.map(u => {
        return {
          id: u.username,
          display: userDisplayName(u),
          avatar: u.avatar,
          email: u.email
        };
      });

      //add beaglebot too!
      users.push(beagle);
      this.setState({ users: users });
    }
  },

  /**
   * onCommentChange(e)
   *
   * update the state of the comment to mirror the user
   * entry (React-ly thinking)
   */
  onCommentChange(e) {
    this.setState({
      comment: e.target.value
    });
  },

  /**
   *onCommentKeyDown(e)
   *
   * process a keydown in the comment entry textarea looking for the
   * ctrl + enter key combo, which will trigger a comment submit
   */
  onCommentKeyDown(e) {
    if (e.ctrlKey && e.keyCode === 13) {
      Intercom('trackUserEvent', 'add-comment(keyboard)');
      this.submitComment();
    }
  },

  /**
  *onAddUserKeyDown(e)
  *
  * process a keydown in the inviteuserInput looking for the
  * enter key, which will trigger an invite to a user
  */
  onAddUserKeyDown(e) {
    //if enter submit the token
    if (e.keyCode === 13) {
      e.preventDefault();
      this.prepareSuggestion();
    }
    //if escape cancel out of add user
    else if (e.keyCode === 27) {
      e.preventDefault();
      this.cancelUserInviteMode();
    }
  },

  /**
  *submitComment()
  *
  * sends the comment state to the submitComment ReportAction
  */
  submitComment() {
    const idx = this.props.sentenceIdx;
    let comment = this.state.comment;
    const { dispatch } = this.props;

    //look for known mentions that weren't selected from the typeahead
    const additionalAtMentionsRegex = /\B@(\w)+/g;
    const additionalAtMentions = comment.match(additionalAtMentionsRegex);
    if (additionalAtMentions) {
      additionalAtMentions.forEach(mention => {
        const potentialUsername = mention.replace('@',''); //lose the '@' and whitespace
        //look for user in suggested users
        const found = _.find(this.state.users, user => {
          return user.id === potentialUsername;
        });
        if (found) {
          //Fabricate - @[id](display)
          const replacement ='@[' + found.id + '](' + found.display + ')';
          //update the comment
          comment = comment.replace(mention, replacement);
        }
      });
    }
    //if there are any included mentions who aren't invited, invite them
    if (this.state.mentionedUsers.length > 0) {
      this.inviteMentions(comment);
    }
    //if the comment isn't empty, submit it
    if (comment) {
      Intercom('trackUserEvent', 'add-comment(mouse)');
      dispatch(submitComment(idx, comment));
      this.setState({ comment: '' });
    }
  },

  /**
  *setInviteUserInputPosition(leftOffset, topOffset)
  *
  * places the absolute positioning of the invite external
  * email input box
  */
  setInviteUserInputPosition(leftOffset, topOffset) {
    const inviteUserInputOverlayEL = this.refs.inviteUserInputOverlay;
    inviteUserInputOverlayEL.style.left = leftOffset;
    inviteUserInputOverlayEL.style.top = topOffset;
  },

  /**
  *prepareSuggestion()
  *
  *
  *
  */
  prepareSuggestion() {
    //store as local variables, the processAddMention variables
    const email = this.refs.inviteUserInput.value.trim();

    //check for valid email format, remain in input mode if failed
    if (!this.validateEmail(email)) {
      const { dispatch } = this.props;
      dispatch(Notification.error(`${email} is an invalid email`));
      return;
    }

    this.onAdd({
      id: email,
      display: email,
      email: email,
    });

    //update the suggestion token to be the entered text from the input
    //switch back to comment mode and replace placeholder with email.
    this.setState({
      inviteUserMode: false,
      comment: this.state.comment.replace('@[add-user](add-user)', `@[${email}](${email})`)
    });
  },

  /**
  *validateEmail(email)
  *
  *if valid email format return true, else false
  *thanks http://stackoverflow.com/a/46181
  */
  validateEmail(email) {
    let re = /^([\w-\+]+(?:\.[\w-\+]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return re.test(email);
  },


  /**
  *renderSuggestion(id, display, search, highlightedDisplay)
  *
  * SuggestionOverylay list contents formatting. formats
  * differently the 'add-user' id
  */
  renderSuggestion(entry) {
    const { id, display } = entry;

    if (id === 'add-user') {
      return (
        <div className="add-user">
          <span><i className="fa fa-plus" /> Add New User</span>
        </div>
      );
    }
    else {
      const user = _.find(this.state.users, u => u.id === id);
      const avatarStyle = { backgroundImage: `url('${user.avatar}')` };
      return (
        <div className="user">
          <div className="suggestion-avatar">
            <div style={avatarStyle} />
          </div>
          <div className="user-details">
            <span className="full-name">{ display }</span>
            <span className="username">{id}</span>
          </div>
        </div>
      );
    }
  },

  isExistingCollaborator(email) {
    const { report } = this.props;
    return report.get('collaborators').find(x => x.get('email') === email);
  },

  isOwner(email) {
    const { report } = this.props;
    const owner = report.get('owner');
    return owner && owner.get('email') === email;
  },

  /*
   * onAdd(suggestion)
   *
   * collects the mentioned users, not already invited to the
   * document in an array
   *
   */
  onAdd(suggestion) {
    //look for beaglebot and don't try to invite
    if (suggestion.id === 'beagle') {
      return;
    }

    if (suggestion.id === 'add-user') {
      //switch into invite user mode
      this.setState({
        inviteUserMode: true
      }, function() {
        //ensure the suggestions dropdown clears
        this.refs.MentionsInput.clearSuggestions();
        //position the input element
        this.setInviteUserInputPosition();
        //force the focus to be on the enter user email
        this.refs.inviteUserInput.focus();
      });
      return;
    }

    //see if the user is an existing collaborator or is the document's owner
    if (!this.isExistingCollaborator(suggestion.email) && !this.isOwner(suggestion.email)) {
      let mentionedUsers = this.state.mentionedUsers;
      //see if they've already been mentioned once
      if (mentionedUsers.indexOf(suggestion.email) === -1) {
        mentionedUsers.push(suggestion);
        this.setState({ mentionedUsers: mentionedUsers });
        //log('ADDED: ', mentionedUsers);
      }
    }
  },

  /*
   * inviteMentions(comment)
   *
   * iterates through the mentionedUsers state and invites all the
   * mentioned users
   *
   */
  inviteMentions(comment) {
    log('INVITE USERS: ', comment);
    //grab the mentionedUsers array
    const mentionedUsers = this.state.mentionedUsers;
    //get the current sentenceIdx
    const { sentenceIdx, dispatch } = this.props;
    //invite all the mentions
    mentionedUsers.forEach(user => {
      if (comment.indexOf(user.id) > -1) {
        dispatch(inviteUser(user.email, sentenceIdx));
      }
    });
    //reset the mentioned users state
    this.setState({ mentionedUsers: [] });
  },

  /**
   *cancelUserInviteMode()
   *
   * Abort the component inviteUserMode and
   * disregard any input text into inviteUserInput.
   */
  cancelUserInviteMode() {
    this.setState({
      inviteUserMode: false,
      mentionDescriptor: null,
      querySequenceStart: null,
      querySequenceEnd: null,
      processAddMention: null
    });
    this.refs.MentionsInput.focusTextarea();
  },

  //the same default filter just with a forced 'Add User' on the end
  queryFunc(query) {
    const data = this.state.users;
    const { isOwner } = this.props;

    var results = [];
    for (var i = 0; i < data.length; i++) {
      var display = data[i].display;
      var id = data[i].id;
      var email = data[i].email;
      if (display.toLowerCase().indexOf(query.toLowerCase()) >= 0 ||
          email.toLowerCase().indexOf(query.toLowerCase()) >= 0 ||
          id.toLowerCase().indexOf(query.toLowerCase()) >= 0) {
        results.push(data[i]);
      }
    }
    //force the last option to be add user if owner
    if (isOwner) {
      results.push({
        id: 'add-user',
        display: 'add-user'
      });
    }

    return results;
  },

  render() {
    const avatarStyle = {
      backgroundImage: `url('${this.props.user.avatar}')`
    };
    const disabledClass = this.state.inviteUserMode ? 'disabled' : null;
    const textStyle = classNames(
      'text', disabledClass
    );

    //comment entry component is an invite window if this.state.inviteUserMode
    var commentEntry;
    var entryButton;
    if (!this.state.inviteUserMode) {
      //entry button is 'submit comment'
      entryButton = (
        <div>
          <Button onClick={this.submitComment}>New comment</Button>
          <span className="small-helper">Ctrl+Enter to Submit</span>
        </div>
      );
      //don't show the invite user input field.
      commentEntry = null;
    }
    else {
      //entry button prompts to invite a user
      entryButton = (
        <div>
          <Button onClick={this.prepareSuggestion}>Invite User</Button>
        </div>
      );
      //comment Entry is a field to invite a user
      commentEntry = (
        <div ref="inviteUserInputOverlay" className="invite-user-overlay">
          <input ref="inviteUserInput" onKeyDown={this.onAddUserKeyDown} placeholder="Invite User Email" />
          <span className="close" onClick={this.cancelUserInviteMode}>
            <i className="fa fa-times" />
          </span>
        </div>
      );
    }

    return (
      <div className="me comment">
        <div className="avatar" style={avatarStyle} />
        <div className={textStyle}>
          <MentionsInput
            spellCheck={false}
            limit={1500}
            ref="MentionsInput"
            className="comment-box react-mentions"
            value={this.state.comment}
            onChange={this.onCommentChange}
            onKeyDown={this.onCommentKeyDown}
            markup="@[__id__](__display__)"
            placeholder={"Mention people using '@'"}
            style={({ '&multiLine': { input: { height: '63px' } } })}>
            <Mention
              type="user"
              trigger="@"
              data={this.queryFunc}
              renderSuggestion={this.renderSuggestion}
              onAdd={this.onAdd}
              appendSpaceOnAdd={true}
            />
          </MentionsInput>
          {commentEntry}
        </div>
        {entryButton}
      </div>
    );
  }

});

const mapNewCommentComponentStateToProps = (state) => {
  return {
    report: state.report,
    isOwner: (
      state.report.get('uuid') && // Make sure that report has been fetched
      state.report.get('owner').get('username') == state.user.get('username')
    )
  }
};

const NewComment = connect(mapNewCommentComponentStateToProps)(NewCommentComponent)


const CommentPanelComponent = React.createClass({

  propTypes: {
    user: React.PropTypes.object.isRequired,
    sentence: React.PropTypes.object.isRequired,
    onChange: React.PropTypes.func
  },

  getInitialState() {
    const initialComments = this.props.sentence.comments;
    return {
      page: 0,
      hasMoreComments: (
        // If true show  moreButton, if false set undefined and don't show any button
        !!initialComments && initialComments.length === COMMENTS_ON_INIT || undefined
      )
    };
  },

  onLoadMore() {
    const idx = this.props.sentence.idx;
    const page = this.state.page + 1;
    const { dispatch } = this.props;

    dispatch(getComments(idx, page))
      .then(resp => {
        this.setState({ page });

        if (resp.data.objects.length < COMMENTS_PER_PAGE) {
          this.setState({ hasMoreComments: false });
        }
      })
      .catch(err => {
        this.setState({ hasMoreComments: false });
        log.error('get comments failed', err)
      });
  },

  deleteComment(uuid) {
    const { dispatch } = this.props;
    const { idx } = this.props.sentence;

    dispatch(deleteCommentOnServer(idx, uuid))
  },

  render() {
    const { user, sentence, collaborators } = this.props;
    const comments = _.chain(sentence.comments)
      .filter(Boolean)
      .sortBy('timestamp')
      .map(c => <Comment key={c.uuid} user={user} comment={c} onDelete={this.deleteComment} />)
      .value();

    return (
      <div className="comment-panel" id="eb-step4">
        <MoreComments onMore={this.onLoadMore}
          hasAnyComments={comments.length > 0}
          hasMoreComments={this.state.hasMoreComments} />
        {comments}
        <NewComment user={user} sentenceIdx={this.props.sentence.idx} collaborators={collaborators} onChange={this.props.onChange} />
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  const c = state.report.get('collaborators').concat([state.report.get('owner')]);
  const collaborators = _.chain(c.toJS())
    .uniqBy(x => x.username)
    .value();

  return {
    report: state.report,
    collaborators
  }
};

export default connect(mapStateToProps)(CommentPanelComponent)
