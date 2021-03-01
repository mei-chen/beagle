var React = require('react');
import _ from 'lodash';
var Reflux = require('reflux');
var Tooltip = require('react-bootstrap/lib/Tooltip');
var Textarea = require('react-textarea-autosize');
var classNames = require('classnames');
var OnClickOutside = require('react-onclickoutside');
var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');

var UserStore = require('common/stores/UserStore');
var LockStore = require('report/stores/LockStore');
var { ReportActions, LockActions } = require('report/actions');

var easing = require('utils/easing');
var TagTools = require('report/components/TagTools');
var CommentPanel = require('report/components/CommentPanel');
var groupedTextDiff = require('utils/groupedTextDiff');
var LINEBREAK_MARKER = require('utils/LINEBREAK_MARKER');
var RevisionControls = require('report/components/RevisionControls');
var LikeTools = require('report/components/LikeTools');
var replaceLineBreaks = require('utils/replaceLineBreak');
var replaceWithLineBreaks = require('utils/replaceWithLineBreak');

require('./styles/EditorBox.scss');


var ClauseView = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
    isLockedOut: React.PropTypes.bool.isRequired,
    text: React.PropTypes.string.isRequired,
    editMode: React.PropTypes.bool.isRequired,
    onPendingTextEditAreaChange: React.PropTypes.func.isRequired,
    setEditMode: React.PropTypes.func.isRequired,
    onSubmit: React.PropTypes.func.isRequired,
    exitEditMode: React.PropTypes.func.isRequired,
  },

  componentDidUpdate() {
    if (this.props.editMode) {
      this.refs.pendingTextEditArea.getDOMNode().focus();
    }
  },

  onClickClause() {
    this.props.setEditMode();
  },

  render() {
    var sentence = this.props.sentence;
    var hasUnapprovedRevision = (sentence.accepted === false && !!sentence.latestRevision);
    var clauseView;
    var isLocked = this.props.isLockedOut;

    var clauseViewClass = classNames(
      'clause-view', {
        'locked': isLocked
      }
    );

    if (!this.props.editMode) {
      var sentenceChildren;
      if (hasUnapprovedRevision) {
        var oldText = sentence.latestRevision.form;
        var newText = sentence.form;
        var deletedColour = 'red';
        var diff = groupedTextDiff(oldText, newText);
        sentenceChildren = _.flatten(diff.map((part, idx) => {
          var spans = [];
          var chunkStyle = {
            color: (part.removed) ? deletedColour : (part.added) ? 'blue' : null,
            textDecoration: (part.removed) ? 'line-through' : null,
          };
          var chunkText = part.value.split('\n');
          // filter to keep only chunks with text inside them
          chunkText.forEach((text, idx2) => {
            spans.push(<span key={`${idx}.${idx2}.span`} style={chunkStyle}>{text}</span>);
            spans.push(<br key={`${idx}.${idx2}.br`} />);
          });
          return _.dropRight(spans);
        }));
      } else {
        var splitText = sentence.form.split(LINEBREAK_MARKER).filter(t => !!t.trim());
        var nodes = [];
        splitText.forEach((str, idx) => {
          nodes.push(<span key={`${idx}.span`}>{str}</span>);
          nodes.push(<br key={`${idx}.br`}/>);
        });
        sentenceChildren = _.dropRight(nodes);
      }

      clauseView = (
        <div className="clause-area" onClick={this.onClickClause}>
          {sentenceChildren}
        </div>
      );
    } else {
      clauseView = (
          <Textarea ref="pendingTextEditArea"
            className={clauseViewClass}
            onChange={this.props.onPendingTextEditAreaChange}
            value={this.props.text}/>
      );
    }

    var lock;
    if (isLocked) {
      var lockOwner = this.props.sentence.lock.owner;
      var lockOwnerName = lockOwner.first_name && lockOwner.last_name ? lockOwner.first_name + ' ' + lockOwner.last_name : lockOwner.email;
      var avatarStyle = {
        backgroundImage: `url('${lockOwner.avatar}')`,
      };

      lock = (
        <div className="sentence-lock">
          <span className="lock-media">
            <span className="lock-avatar" style={avatarStyle} />
            <span className="lock-icon">
              <i className="fa fa-lock" />
            </span>
          </span>
          <span className="lock-info">
            <span className="lock-name">{lockOwnerName}</span>
            <span className="lock-description">Locked for editing</span>
          </span>
        </div>
      );
    }

    return (
      <div className={clauseViewClass}>
        {clauseView}
        {lock}
      </div>
    );
  }

});


var EditorBox = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
    disableEditMode: React.PropTypes.func.isRequired,
  },

  mixins: [
    Reflux.connect(UserStore, 'user'),
    Reflux.connect(LockStore, 'locks'),
    OnClickOutside
  ],

  getInitialState() {
    return {
      comment: this.props.sentence.comment || '',
      text: replaceLineBreaks(this.props.sentence.form),
      editMode: false,
      textChanged: false,
      introJsObject: null
    };
  },

  componentDidMount() {
    this.animateOpen();
    //evoke the intro wizard (function will decide if relevant)
    this.introJsEditorBoxEvoke()
  },

  //Starts the editor box overlay intro wizard
  introJsEditorBoxEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof introJs !== 'undefined' && !INTROJS_STEPS_EDITOR_BOX_DONE) {
      var intro = introJs();
      intro.setOptions(INTROJS_STEPS_EDITOR_BOX);
      intro.start();
      intro.oncomplete(this.removeIntroJsState);
      intro.onexit(this.removeIntroJsState);
      this.setState({ introJsObject : intro });
      INTROJS_STEPS_EDITOR_BOX_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  //Housekeeping: clear away the introJs object state varible when done with it.
  removeIntroJsState() {
    this.setState({ introJsObject : null  });
  },


  componentWillReceiveProps(nextProps) {
    //make sure that the text is updated in case of an edit from another user
    var newText = replaceLineBreaks(nextProps.sentence.form);
    this.setState({ text: newText });
  },

  componentWillUpdate(nextProps, nextState) {
    if (nextState.editMode === true) {
      this.requestLock();
    } else if (nextState.editMode === false) {
      this.releaseLock();
    }
  },

  componentDidUnmount() {
    this.releaseLock();
  },

  animateOpen() {
    // animate the editor window
    var node = this.getDOMNode();
    var styles = window.getComputedStyle(node);
    var targetHeight = parseInt(styles.getPropertyValue('height'), 10);

    // initial state: height 0, show no overflow
    node.style.height = '0px';
    node.style.overflow = 'hidden';

    // animation settings
    var start = null;
    var animationLength = targetHeight + 150; // milliseconds
    var easingFn = easing.easeOutCubic;

    // this is the function that executes on each animation frame
    var animateFrame = function(timestamp) {
      if (!start) {
        start = timestamp; // initialize start time
      }
      var elapsed = timestamp - start;
      var percentDone = elapsed / animationLength;
      var easedPercentDone = easingFn(percentDone);
      var stepHeight = targetHeight * easedPercentDone;
      var nodeHeight = `${stepHeight}px`;
      node.style.height = nodeHeight;
      if (percentDone < 1) {
        requestAnimationFrame(animateFrame);
      } else {
        node.style.height = null;
        node.style.overflow = null;
      }
    };
    // animate!
    requestAnimationFrame(animateFrame);
  },

  requestLock() {
    var idx = this.props.sentence.idx;
    LockActions.requestLock(idx);
  },

  releaseLock() {
    var idx = this.props.sentence.idx;
    LockActions.releaseLock(idx);
  },

  reset() {
    this.setState({ text: this.props.sentence.form });
  },

  setEditMode() {
    this.requestLock();
    this.setState({ editMode: true });
  },

  exitEditMode() {
    this.releaseLock();
    this.setState({ editMode: false });
  },

  onClose() {
    this.releaseLock();
    this.props.disableEditMode();
  },

  onSubmit() {
    var idx = this.props.sentence.idx;
    // save text if changes were made
    var text = replaceWithLineBreaks(this.state.text);
    var initialText = this.props.sentence.form;
    if (text !== initialText) {
      ReportActions.editText(idx, text);
      ReportActions.saveSentence(idx);
    }
    this.exitEditMode();
  },

  handleClickOutside() {
    if (!this.state.introJsObject && !this.state.textChanged) { //disable click outside for the introJS
      this.onSubmit();
      this.onClose();
    }
  },

  onClickCloseBtn() {
    // don't save
    this.onClose();
  },

  onPendingTextEditAreaChange(evt) {
    var text = evt.target.value;
    this.setState({
      text: text,
      textChanged: true
    });
  },

  onAcceptChange() {
    var idx = this.props.sentence.idx;
    ReportActions.acceptChange(idx);
    this.props.disableEditMode();
  },

  onRejectChange() {
    var idx = this.props.sentence.idx;
    ReportActions.rejectChange(idx);
    this.props.disableEditMode();
  },

  render() {
    var user = this.state.user;
    var sentence = this.props.sentence;

    var hasUnapprovedRevision = !!sentence.latestRevision;

    var lock = sentence.lock;
    var isLockedOut = lock !== null && lock.owner.username !== user.username;

    var text = replaceWithLineBreaks(this.state.text);

    var textPending = !!text && text !== sentence.form;
    var textDeletePending = text === '';

    var boxStyle = classNames(
      'beagle-editor-box-mobile', {
        'regular': !this.props.isInList,
        'is-in-list': this.props.isInList,
      }
    );

    var closeBtnStyle = classNames(
      'close-btn', {
        'no-close-btn': this.props.noCloseBtn,
      }
    );

    var closeBtn = (
      <div className={closeBtnStyle} onClick={this.onClickCloseBtn}>
        <i className="fa fa-remove" />
      </div>
    );

    // computes a small string that is kind of unique for the tags and suggested
    // tags that are on the sentence object so that the TagTools component
    // re-renders when tags change
    const tagsHash = 'tags-' +
      '?' + (sentence.tags || []).map(t => t[0]).join('') +
      '!' + (sentence.suggested_tags || []).map(t => t[0]).join('');

    return (
      <div className={boxStyle} id="eb-step1">
        {closeBtn}
        <div className="editor-contents">
          <div className="textarea-contents" id="eb-step2">
            <ClauseView sentence={sentence}
              onPendingTextEditAreaChange={this.onPendingTextEditAreaChange}
              text={this.state.text}
              editMode={this.state.editMode}
              isLockedOut={isLockedOut}
              setEditMode={this.setEditMode}
              onSubmit={this.onSubmit}
              exitEditMode={this.exitEditMode} />
          </div>
          <div className="bottom-controls">
            <LikeTools
              username={user.username}
              sentence={sentence} />
            <RevisionControls
              pending={textPending}
              deletePending={textDeletePending}
              unapproved={hasUnapprovedRevision}
              acceptChange={this.onAcceptChange}
              rejectChange={this.onRejectChange}
              submitRevision={this.onSubmit} />
          </div>
          <TagTools
            key={tagsHash}
            user={user}
            sentence={sentence} />
          <div className="control-panel">
            <CommentPanel sentence={sentence} user={user} />
          </div>
        </div>
      </div>
    );
  }

});


module.exports = EditorBox;
