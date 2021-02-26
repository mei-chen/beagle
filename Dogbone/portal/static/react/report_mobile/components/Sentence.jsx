import _ from 'lodash';
var React = require('react');
var ReactDOM = require('react-dom');
var $ = require('jquery');
var Tooltip = require('react-bootstrap/lib/Tooltip');
var classNames = require('classnames');
var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');

var ReportStore = require('report/stores/ReportStore');
var { ReportActions } = require('report/actions');

var EditorBox = require('./EditorBox');
var breakLines = require('utils/insertLineBreaks');
var groupedTextDiff = require('utils/groupedTextDiff');
var LINEBREAK_MARKER = require('utils/LINEBREAK_MARKER');
var splitExternalReferences = require('utils/splitExternalReferences');

const styles = require('./styles/Sentence.scss');
require('utils/constants.js');


var Sentence = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
    isActive: React.PropTypes.bool,
    liabActive: React.PropTypes.bool.isRequired,
    respActive: React.PropTypes.bool.isRequired,
    termActive: React.PropTypes.bool.isRequired,
    refsActive: React.PropTypes.bool.isRequired,
    enableEditMode: React.PropTypes.func.isRequired,
    disableEditMode: React.PropTypes.func.isRequired,
    onFocusCallback: React.PropTypes.func,
    isModalView: React.PropTypes.bool
  },

  getDefaultProps() {
    return {
      onFocusCallback: null,
      editingSentenceIdx: null,
      focusedSentenceIdx: null,
    };
  },

  getInitialState() {
    return {
      pendingText: null
    };
  },

  componentDidMount() {
    this.focusEditorBoxIfNeeded();
  },

  componentDidUpdate(oldProps) {
    this.redrawSentenceIfNeeded(oldProps);
    this.focusEditorBoxIfNeeded(oldProps);
  },

  forceWebkitRedraw() {
    // thanks http://stackoverflow.com/a/14382251
    var el = this.getDOMNode();
    var displayMode = $(el).css('display');
    $(el).css('display', 'none').height();
    $(el).css('display', displayMode);
  },

  clearPendingText() {
    this.setState({ pendingText: null });
  },

  onSaveSentenceText() {
    var idx = this.props.sentence.idx;
    var newText = this.state.pendingText;
    ReportActions.editText(idx, newText);
    ReportActions.saveSentence(idx);
    this.clearPendingText();
  },

  onCancelEditSentence() {
    this.clearPendingText();
  },

  /**
   * redrawSentenceIfNeeded
   *
   * This is a bit of a hack. In Chrome, the issue underline colour wasn't
   * changing when the issue changed until you hover over a sentence. This
   * forces the sentence to redraw in the browser with the right underline
   * colour.
   *
   * @param {object} oldProps props from the previous render of this component
   * (call this method from componentDidUpdate)
   */
  redrawSentenceIfNeeded(oldProps) {
    var oldIssue = oldProps.sentence.likes;
    var newIssue = this.props.sentence.likes;
    if (oldIssue !== newIssue) {
      this.forceWebkitRedraw();
    }
  },

  /**
   * focusEditorBoxIfNeeded
   *
   * If the edit mode for this sentence has changed since the last render, the
   * window will automatically focus the screen on this sentence (the scroll
   * position will reveal the open EditorBox).
   *
   * When the focus animation completes, this will invoke
   * `this.props.onFocusCallback` if it is supplied.
   *
   * @param {?object} oldProps (default = {})
   * this method was written to be called from `componentDidUpdate`, and from
   * there we pass down the component props. They are used to tell whether the
   * edit mode has changed. Defaults to empty object when this is called from
   * `componentDidMount`, no `oldProps` are available.
   */
  focusEditorBoxIfNeeded(oldProps = {}) {
    let { focusedSentenceIdx, sentence } = this.props;
    let { idx } = sentence;
    let isFocused = focusedSentenceIdx === idx;

    let prevEditMode = oldProps.editingSentenceIdx === idx;
    let currEditMode = this.props.editingSentenceIdx === idx;
    let editModeWasEnabled = currEditMode && !prevEditMode;

    if (isFocused || editModeWasEnabled) {
      let editorBox = React.findDOMNode(this);
      let editorBoxAbsOffsetTop =
        editorBox.offsetTop + editorBox.offsetParent.offsetTop;

      let newScrollTop = editorBoxAbsOffsetTop - screen.height / 6;
      let animProps = { scrollTop: newScrollTop };
      let callback = this.props.onFocusCallback;
      $('body').animate(animProps, callback);
    }
  },

  onSentenceClick() {
    this.props.enableEditMode();
    //if introJs
    if (!!this.props.introJsObject && !INTROJS_STEPS_EDITOR_BOX_DONE) {
      //kill the running introJs wizard
      console.log("INTRO EXIT?: ", this.props.introJsObject);
      this.props.introJsObject.exit()
    }
  },

  onOverlayClick() {
    this.props.disableEditMode();
  },

  render() {
    const sentence = this.props.sentence;

    // this is a new line only. no text to display and no render logic required
    if (sentence.form.trim() === '' && sentence.newlines > 0) {
      return <div key={sentence.idx} className={styles.linebreak}><br/></div>;
    }

    var editingSentenceIdx = this.props.editingSentenceIdx;
    var isEditing = editingSentenceIdx === sentence.idx;
    var noneEditing = editingSentenceIdx === null;
    var otherEditing = !isEditing && !noneEditing;

    if (isEditing) {
      return (
        <EditorBox
          sentence={sentence}
          isCondensed={this.props.isModalView}
          isClauseTable={false}
          disableEditMode={this.props.disableEditMode}/>
      );
    }

    var hasAnnotations = !!sentence.annotations ? ((sentence.annotations.filter(a => {return a.type === ANNOTATION_TAG_TYPE} )) || []).length > 0 : false;
    var annotations = hasAnnotations ? sentence.annotations.filter(a => {return a.type === ANNOTATION_TAG_TYPE} ) : [];
    var extRefs = sentence.external_refs || [];
    var hasExternalReferences = extRefs.length > 0;

    var focusedSentenceIdx = this.props.focusedSentenceIdx;
    var isFocused = !isEditing && !otherEditing && (focusedSentenceIdx === sentence.idx);
    var noneFocused = focusedSentenceIdx === null;

    var liabIsEnabled = noneFocused && this.props.liabActive;
    var respIsEnabled = noneFocused && this.props.respActive;
    var termIsEnabled = noneFocused && this.props.termActive;
    var refsAreEnabled = noneFocused && this.props.refsActive;

    var isResponsibility = hasAnnotations && annotations[0].label === 'RESPONSIBILITY';
    var isLiability = hasAnnotations && annotations[0].label === 'LIABILITY';
    var isTermination = hasAnnotations && annotations[0].label === 'TERMINATION';

    var isDeleted = sentence.deleted === true;

    var username = ReportStore.getUserName();
    var hasOpinions = !!sentence.likes;
    var hasLikes = hasOpinions && sentence.likes.likes.length > 0;
    var hasDislikes = hasOpinions && sentence.likes.dislikes.length > 0;
    var userDoesLike = hasLikes && _.contains(sentence.likes.likes, username);
    var userDoesDislike = hasDislikes && _.contains(sentence.likes.dislikes, username);
    var hasManualTags = !!sentence.annotations ? ((sentence.annotations.filter(a => {return a.type === MANUAL_TAG_TYPE} )) || []).length > 0 : false;
    var hasSuggestedTags = !!sentence.annotations ? ((sentence.annotations.filter(a => {return a.type === SUGGESTED_TAG_TYPE})) || []).length > 0 : false;
    var isLocked = sentence.lock !== null;

    var isActive = (isFocused) ||
      (isResponsibility && respIsEnabled) ||
      (isLiability && liabIsEnabled) ||
      (isTermination && termIsEnabled);

    var sentenceClasses = classNames({
      [styles.sentence]: true,
      'beagle-report-sentence': true,
      'locked': isLocked,
      'deleted': isDeleted,
      'focused': isFocused,
      'ignore-react-onclickoutside': isEditing,
    });

    var textClasses = classNames({
      'sentence-text': true,
      'style-bold': sentence.style ? sentence.style.bold : false,
      'style-underline': sentence.style ? sentence.style.underline : false,
      'annotation': hasAnnotations,
      'active': isActive,
      'resp': isResponsibility,
      'liab': isLiability,
      'term': isTermination,
      'tagged': hasManualTags,
      'auto-tagged': !hasManualTags && hasSuggestedTags,
    });

    var deletedColour = 'red';

    var sentenceStyles = {};
    var underlineStyles = {};
    var textStyles = {};
    if (sentence.style) {
      textStyles.fontSize = (11 + (sentence.style.size || 0)) + 'pt';
    }

    if (userDoesLike || userDoesDislike) {
      _.assign(underlineStyles, {
        color: (userDoesLike) ? 'green' : (userDoesDislike) ? 'red' : null,
        textDecoration: 'underline'
      });
      _.assign(textStyles, {
        color: 'black' // initial
      });
    }

    // handle entire sentence deleted styles
    if (isDeleted) {
      _.assign(sentenceStyles, {
        color: deletedColour,
        textDecoration: 'line-through'
      });
      _.assign(textStyles, {
        color: deletedColour
      });
    }

    var refClasses = classNames(
      'annotation',
      'refs',
      (refsAreEnabled || isFocused) ? 'active' : null
    );

    // will be an array of nodes.
    // broken up due to line breaks, diff, ext refs...
    var sentenceChildren;

    var hasUnapprovedRevision = (sentence.accepted === false && !!sentence.latestRevision);

    if (hasUnapprovedRevision) {
      var oldText = sentence.latestRevision.form;
      var newText = sentence.form;

      var diff = groupedTextDiff(oldText, newText);

      sentenceChildren = _.flatten(diff.map((part, idx) => {
        var chunkStyle = {
          color: (part.removed) ? deletedColour : (part.added) ? 'blue' : null,
          textDecoration: (part.removed) ? 'line-through' : null,
        };
        var children = [];
        part.value.split('\n').forEach(splitSubstring => {
          children.push(<span key={`${idx}.span`} style={chunkStyle}>{splitSubstring}</span>);
          children.push(<br key={`${idx}.br`}/>);
        });
        return _.dropRight(children);
      }));
    }
    else if (hasExternalReferences) {
      var strings = splitExternalReferences(sentence);
      sentenceChildren = _.flatten(strings.map(string => {
        var childRefClasses = string.ref === true ? refClasses : null;
        var splitStrings = string.text.split(LINEBREAK_MARKER);
        var nodes = [];
        splitStrings.forEach((str, idx2) => {
          nodes.push(<span key={idx2 + 'sp'} className={childRefClasses}>{str}</span>);
          nodes.push(<br key={idx2 + 'br'}/>);
        });
        return _.dropRight(nodes);
      }));
    }
    else {
      sentenceChildren = [sentence.form];
    }

    if (sentence.contains_linebreaks) {
      var splitChildren = [];
      sentenceChildren.forEach(child => {
        splitChildren.push(breakLines(child));
      });
      sentenceChildren = _.flatten(splitChildren);
    }

    var comment;
    var comments = (sentence.comments || []).filter(c => c != null);
    var filteredComments = comments.filter(comm => {
      return comm.author.username !== '@beagle';
    });
    var sortedUniqueCommentorNames = _.sortBy(_.uniq(filteredComments.map(comm => {
      return comm.author.first_name || comm.author.username;
    })));
    var commentorNames = sortedUniqueCommentorNames.map(name => {
      return <li key={name}><strong>{name}</strong></li>;
    });
    var commentorNamesTooltip = <Tooltip><ul className="tooltip-ul">{commentorNames}</ul></Tooltip>;
    if (sentence.comments) {
      comment = (
        <OverlayTrigger placement="top" overlay={commentorNamesTooltip}>
          <i onClick={this.onSentenceClick} className="fa fa-comment comments"/>
        </OverlayTrigger>
      );
    }

    var suggestedTags;
    if (hasSuggestedTags) {
      var suggestedTagsObjects = sentence.annotations.filter(a => {return a.type===SUGGESTED_TAG_TYPE});
      var suggTagsNames = 'Suggested tags: ' + sentence.annotations.map(a => {return a.label}).join(', ');

      var suggTagsTooltip = <Tooltip>{suggTagsNames}</Tooltip>;
      suggestedTags = (
        <OverlayTrigger placement="top" overlay={suggTagsTooltip}>
          <i onClick={this.onSentenceClick} className="fa fa-tag comments"/>
        </OverlayTrigger>
      );
    }

    // assign a sequential key to every sentence child
    sentenceChildren = sentenceChildren.map((child, idx) => {
      if (child.props) { // is a ReactElement
        var newProps = _.assign(child.props, { key: idx });
        return React.cloneElement(child, newProps);
      } else { // is just a string
        return child;
      }
    });

    //if there is a sentence lock, display the locked users icon
    var lockIcon;
    if (sentence.lock) {
      var lockOwner = sentence.lock.owner;
      var avatarStyle = {
        backgroundImage: `url('${lockOwner.avatar}')`,
      };
      lockIcon = (
        <div className="icon-right">
          <span className="lock-media">
            <span className="lock-avatar" style={avatarStyle} />
            <span className="lock-icon">
              <i className="fa fa-lock" />
            </span>
          </span>
        </div>
      );
    }

    var newlines = [];
    for (var i = 0; i < Math.min(sentence.newlines, 10); i++) {
      newlines.push(<br key={i + 'trail-br'}/>);
    }

    return (
      <span className={sentenceClasses} style={sentenceStyles} onClick={this.onSentenceClick}>
        <span style={underlineStyles}>
          <span className={textClasses} style={textStyles}>
            {sentenceChildren}
          </span>
        </span>
        {comment}
        {suggestedTags}
        {lockIcon}
        {newlines}
      </span>
    );
  }

});


module.exports = Sentence;
