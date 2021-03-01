/* NPM Modules */
import _ from 'lodash';
import React from 'react';
import classNames from 'classnames';
import uuidV4 from 'uuid/v4';

/* Utilities */
import replaceLineBreak from 'utils/replaceLineBreak';
import groupedTextDiff from 'utils/groupedTextDiff';
import LINEBREAK_MARKER from 'utils/LINEBREAK_MARKER';
import ILVL_MARKER from 'utils/INDENTLEVEL_MARKER';
import insertIndents from 'utils/insertIndents';

/* Bootstrap Requirements */
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

/* Components */
import TagTools from '../TagTools';
import LikeTools from '../LikeTools';
import EditorBox from '../EditorBox';
import CommentPanel from '../CommentPanel';

/* Style */
require('./styles/ClauseTableBody.scss');

const Clause = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
    user: React.PropTypes.object.isRequired,
    query : React.PropTypes.string.isRequired,
    onSelectClauseCheck : React.PropTypes.func.isRequired,
    isSelected : React.PropTypes.bool.isRequired,
  },

  getInitialState() {
    return {
      commentMode : this.props.commentMode,
      editMode : false,
      isSelected : this.props.isSelected,
    };
  },

  toggleCommentMode() {
    var toggle = !this.state.commentMode;
    this.setState({ commentMode : toggle });
  },

  onCommentIndicatorClick() {
    this.toggleCommentMode();
  },

  onSelectClauseCheck(e) {
    this.setState({ isSelected : !this.state.isSelected });
    this.props.onSelectClauseCheck(e, this.props.sentence.idx);
  },

  generateEditIcon() {
    if (!this.props.sentence.accepted) {
      var editMessage = (
        <Tooltip id="1">
          <strong>Sentence edited</strong>
        </Tooltip>
      );

      return (
        <OverlayTrigger placement="right" overlay={editMessage}>
          <div className="edit-indicator-container">
            <i className="fa fa-clock" />
            <div className="alerts">
              <i className="fa fa-pencil"/>
            </div>
          </div>
        </OverlayTrigger>
      );
    } else {
      return (
        <div className="edit-indicator-container disabled">
          <i className="fa fa-clock" />
        </div>
      );
    }
  },

  generateLikeIcons() {
    return (
      <LikeTools
        username={this.props.user.username}
        sentence={this.props.sentence}
      />
    );
  },

  generateCommentIcon() {
    var message = this.state.commentMode ? 'Hide comments' : 'Add a comment';
    var addCommentMessage = (
      <Tooltip id="2">
        <strong>{message}</strong>
      </Tooltip>
    );
    var commentsCount = this.props.sentence.comments_count || 0;

    if (commentsCount > 0) {
      return (
        <OverlayTrigger placement="right" overlay={addCommentMessage}>
          <div className="comment-indicator">
            <div className="comment-indicator-container" onClick={this.onCommentIndicatorClick}>
              <i className="fa fa-comment" />
              <div className="alerts">
                <span>{(commentsCount > 99) ? '99+' : commentsCount}</span>
              </div>
            </div>
          </div>
        </OverlayTrigger>
      );
    } else {
      return (
        <OverlayTrigger placement="right" overlay={addCommentMessage}>
          <div className="comment-indicator" onClick={this.onCommentIndicatorClick}>
            <div className="comment-indicator-container disabled">
              <i className="fa fa-comment" />
            </div>
          </div>
        </OverlayTrigger>
      );
    }
  },

  disableEditMode() {
    this.setState({ editMode : false });
  },

  enableEditMode() {
    this.setState({ editMode : true });
  },

  specialCharRegex(str) {
    str = str.replace(/[\-\-\–\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, '\\$&');
    str = str.replace(/"/g,'[\\"\\\“\\\”]'); //consider all quotes the same "“”
    return new RegExp(str, 'gi');
  },

  getRedlineSpans() {
    var sentence = this.props.sentence;
    var deletedColour = 'red';
    var oldText = sentence.latestRevision.form;
    var newText = sentence.form;

    var diff = groupedTextDiff(oldText, newText);

    return _.flatten(diff.map((part) => {
      var chunkStyle = {
        color: (part.removed) ? deletedColour : (part.added) ? 'blue' : null,
        textDecoration: (part.removed) ? 'line-through' : null,
      };
      var children = [];
      part.value.split(LINEBREAK_MARKER).forEach((splitSubstring) => {
        children.push(<span key={uuidV4()} style={chunkStyle}>{insertIndents(splitSubstring)}</span>);
        children.push(<br key={uuidV4()}/>);
      });
      return _.dropRight(children);
    }));
  },

  generateClauseForm() {
    var sentence = this.props.sentence;
    var text = replaceLineBreak(sentence.form);
    var hasUnapprovedRevision = (sentence.accepted === false && !!sentence.latestRevision);
    var spans = [];
    let searchRegex;

    //If the user has a query entered and there are redlines to display
    if (hasUnapprovedRevision && this.props.query) {
      spans = this.getRedlineSpans();
      var newSpans = [];
      searchRegex = this.specialCharRegex(this.props.query);

      spans.forEach(span => {
        //if the match is inside a span element
        if (span.props.children.toLowerCase().indexOf(this.props.query.toLowerCase()) > -1) {
          var spanMatches = span.props.children.match(searchRegex);
          var spanRuns = span.props.children.split(searchRegex);
          var spanMatchesLength = spanMatches ? spanMatches.length : 0; //important to grab length because the for loop shifts elements off as it iterates
          var innerSpans = [];
          innerSpans.push(<span key={uuidV4()}>{spanRuns.shift()}</span>);
          for (var i = 0; i < spanMatchesLength; i++) {
            innerSpans.push(<span key={uuidV4()} className="query-match">{spanMatches.shift()}</span>);
            innerSpans.push(<span key={uuidV4()}>{spanRuns.shift()}</span>);
          }
          span = (<span key={uuidV4()} style={span.props.style}>{innerSpans}</span>);
        }
        newSpans.push(span);
      });
      spans = newSpans;
    //if only a query is to be highlighted
    } else if (this.props.query) {
      searchRegex = this.specialCharRegex(this.props.query);
      //this.specialCharRegex(searchRegex);
      var matches = text.match(searchRegex);
      var matchesLength = matches ? matches.length : 0;
      var sentenceRuns = text.split(searchRegex);
      spans.push(<span key={uuidV4()}>{sentenceRuns.shift()}</span>);
      for (var i = 0; i < matchesLength; i++) {
        spans.push(<span key={uuidV4()} className="query-match">{matches.shift()}</span>);
        spans.push(<span key={uuidV4()}>{sentenceRuns.shift()}</span>);
      }
      //if only redlines are to be displayed
    } else if (hasUnapprovedRevision) {
      spans = this.getRedlineSpans();
    } else {
      const ilvlRegExp = new RegExp(ILVL_MARKER);
      const split = text.split(ilvlRegExp);

      if (split.length === 1) {
        spans.push(<span key={uuidV4()}>{insertIndents(text)}</span>);
      } else {
        split.forEach((txt, idx) => {
          if (idx % 2 == 0) {
            spans.push(<span key={uuidV4()}>{insertIndents(txt)}</span>);
            spans.push(<br key={`${idx}.br`}/>);
          }
        });
      }
    }

    return (
      <div className="sentence" onClick={this.enableEditMode}>
        {spans}
      </div>
    );
  },

  generateEditBox() {
    return (
      <EditorBox
        isCondensed isClauseTable
        sentence={this.props.sentence}
        disableEditMode={this.disableEditMode}
      />
    );
  },

  generateCheckbox() {
    return (
      <div className="check-tools">
        <input onChange={this.onSelectClauseCheck} checked={this.props.isSelected} type="checkbox" />
      </div>
    );
  },

  render() {
    let { sentence, user } = this.props;
    var editIcon = this.generateEditIcon();
    var commentIcon = this.generateCommentIcon();
    var commentPanel;
    if (this.state.commentMode) {
      commentPanel = <CommentPanel sentence={sentence} user={user} />;
    }
    var likeIcons = this.generateLikeIcons();
    var clauseForm = this.generateClauseForm();
    var checkBox = this.generateCheckbox();
    var clauseStyle = classNames(
      'clause',
      { 'selected' : this.props.isSelected }
    );
    //to properly update the tag tools when a new tag exists, you need to provide a
    //unique key each time. TODO: figure out wtf makes that so.
    var tagToolKey = this.props.sentence.annotations ? this.props.sentence.annotations.length : 0;
    if (this.state.editMode) {
      return this.generateEditBox()
    }
    else {
      return (
        <div className="clause-container">
          <div className={clauseStyle}>
            <div className="clause-body">
              <div className="clause-tools">
                {likeIcons}
                {checkBox}
              </div>
              <div className="center-pane">
                {clauseForm}
                <div className="tag-tools">
                  <TagTools
                    key={tagToolKey}
                    user={user}
                    sentence={this.props.sentence}
                  />
                </div>
              </div>
              <div className="edit-indicator">
                {editIcon}
                {commentIcon}
              </div>
            </div>
            <div className="comment-pane">
              {commentPanel}
            </div>
          </div>
        </div>
      );
    }
  }
});



const Clauses = React.createClass({
  propTypes: {
    sentences: React.PropTypes.array.isRequired,
    query : React.PropTypes.string.isRequired,
    onSelectClauseCheck : React.PropTypes.func.isRequired,
    allSelected : React.PropTypes.array.isRequired,
    user: React.PropTypes.object.isRequired,
  },

  getSentences() {
    const sentences = this.props.sentences;
    if (sentences.length > 0) {
      return (
        sentences.map(sentence => {
          return (
            <Clause
              commentMode={this.props.commentMode}
              key={sentence.idx}
              sentence={sentence}
              user={this.props.user}
              query={this.props.query}
              onSelectClauseCheck={this.props.onSelectClauseCheck}
              isSelected={this.props.allSelected.indexOf(sentence.idx) > -1}
            />
          );
        })
      );
    }
    else {
      return (
        <div className="empty-search">
          <span>Sorry, no clauses found</span>
        </div>
      );
    }
  },

  render() {
    var clauses = this.getSentences();
    return (
      <div className="clauses">
        {clauses}
      </div>
    );
  }
});

var ClauseTableBody = React.createClass({

  propTypes: {
    sentences: React.PropTypes.array.isRequired,
    query : React.PropTypes.string.isRequired,
    onSelectClauseCheck : React.PropTypes.func.isRequired,
    allSelected : React.PropTypes.array.isRequired,
    user: React.PropTypes.object.isRequired,
  },

  render() {
    return (
      <div className="clause-table-body">
        <Clauses
          commentMode={this.props.commentMode}
          user={this.props.user}
          sentences={this.props.sentences}
          query={this.props.query}
          onSelectClauseCheck={this.props.onSelectClauseCheck}
          allSelected={this.props.allSelected}
        />
      </div>
    );
  }
});

module.exports = ClauseTableBody;
