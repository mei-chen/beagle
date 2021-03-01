import _ from 'lodash';

import React from 'react';
import { connect } from 'react-redux';
import Tooltip from 'react-bootstrap/lib/Tooltip';

import classNames from 'classnames';
import OnClickOutside from 'react-onclickoutside';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import uuidV4 from 'uuid/v4';

import easing from 'utils/easing';
import ConfirmDeleteModal from './ConfirmDeleteModal';
import TagTools from './TagTools';
import CommentPanel from './CommentPanel';
import groupedTextDiff from 'utils/groupedTextDiff';
import LINEBREAK_MARKER from 'utils/LINEBREAK_MARKER';
import RevisionControls from './RevisionControls';
import LikeTools from './LikeTools';
import replaceLineBreaks from 'utils/replaceLineBreak';
import replaceWithLineBreaks from 'utils/replaceWithLineBreak';
import insertIndents from 'utils/insertIndents';
import CustomEditor from 'common/components/CustomEditor';
import {
  releaseLock,
  requestLock,
  submitEditSentence,
  acceptChange,
  rejectChange
} from 'report/redux/modules/report';
require('./styles/EditorBox.scss');


const ClauseView = React.createClass({

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

  onClickClause() {
    this.props.setEditMode();
  },

  renderEditor() {
    return (
      <CustomEditor
        ref="pendingTextEditArea"
        onChange={this.props.onPendingTextEditAreaChange}
        text={this.props.text}
      />
    );
  },

  render() {
    const sentence = this.props.sentence;
    const hasUnapprovedRevision = (sentence.accepted === false && !!sentence.latestRevision);
    let clauseView;
    const isLocked = this.props.isLockedOut;

    const clauseViewClass = classNames(
      'clause-view', {
        'locked': isLocked
      }
    );

    if (!this.props.editMode) {
      let sentenceChildren;
      if (hasUnapprovedRevision) {
        const oldText = sentence.latestRevision.form;
        const newText = sentence.form;
        const deletedColour = 'red';
        const insertedColour = 'blue';
        const diff = groupedTextDiff(oldText, newText);

        sentenceChildren = _.flatten(diff.map((part, idx) => {
          const spans = [];
          const chunkStyle = {
            color: (part.removed) ? deletedColour : (part.added) ? insertedColour : null,
            textDecoration: (part.removed) ? 'line-through' : null,
          };
          // LINEBREAK_MARKERs were already replaced with '\n' in groupedTextDiff,
          // so there aren't any LINEBREAK_MARKERs in diff's parts
          const chunkText = part.value.split('\n');
          // filter to keep only chunks with text inside them
          chunkText.forEach((text, idx2) => {
            spans.push(<span key={`${idx}.${idx2}.span`} style={chunkStyle}>{insertIndents(text)}</span>);
            spans.push(<br key={`${idx}.${idx2}.br`} />);
          });
          return _.dropRight(spans);
        }));
      } else { // End of hasUnapprovedRevision
        var splitText = sentence.form.split(LINEBREAK_MARKER).filter(t => !!t.trim());
        var nodes = [];
        splitText.forEach((str, idx) => {
          nodes.push(<span key={`${idx}.span`}>{insertIndents(str)}</span>);
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
      clauseView = this.renderEditor();
    }

    let lock;
    if (isLocked) {
      const lockOwner = this.props.sentence.lock.owner;
      const lockOwnerName = lockOwner.first_name && lockOwner.last_name ? lockOwner.first_name + ' ' + lockOwner.last_name : lockOwner.email;
      const avatarStyle = {
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


const EditorBoxComponent = OnClickOutside(React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
    isCondensed: React.PropTypes.bool,
    disableEditMode: React.PropTypes.func.isRequired,
  },

  getInitialState() {
    return {
      comment: this.props.sentence.comment || '',
      text: replaceLineBreaks(this.props.sentence.form),
      editMode: false,
      textChanged: false,
      introJsObject: null,
      isSubmitting: false,
      isUnsavedComment: false,
      isConfirmDeleteOpen: false
    };
  },

  componentDidMount() {
    this.animateOpen();
    //evoke the intro wizard (function will decide if relevant)
    this.introJsEditorBoxEvoke()
  },

  componentWillReceiveProps(nextProps) {
    const user = this.props.user.toJS();
    const lock = nextProps.sentence.lock;
    const hasLock = lock && lock.owner.username === user.username;

    // Prevent rerenders replacing the text
    if (!hasLock) {
      //make sure that the text is updated in case of an edit from another user
      const newText = replaceLineBreaks(nextProps.sentence.form);
      this.setState({ text: newText });
    }
  },

  componentWillUnmount() {
    this.releaseLock();
  },

  //Housekeeping: clear away the introJs object state varible when done with it.
  removeIntroJsState() {
    this.setState({ introJsObject : null });
  },


  //
  /**
   * @deprecated as has constants that's not defined anywhere in the module and is not imported
   * @summary Starts the editor box overlay intro wizard
   */
  introJsEditorBoxEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof window.introJs !== 'undefined' && !window.INTROJS_STEPS_EDITOR_BOX_DONE) {
      var intro = window.introJs();
      intro.setOptions(window.INTROJS_STEPS_EDITOR_BOX);
      intro.start();
      intro.oncomplete(this.removeIntroJsState);
      intro.onexit(this.removeIntroJsState);
      this.setState({ introJsObject : intro });
      window.INTROJS_STEPS_EDITOR_BOX_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  animateOpen() {
    // animate the editor window
    var node = this.refs.editorBox;
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
    const { sentence, dispatch } = this.props;
    dispatch(requestLock(sentence.idx))
  },

  releaseLock() {
    const { sentence, dispatch } = this.props;
    dispatch(releaseLock(sentence.idx))
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
    const { dispatch, sentence } = this.props;
    const idx = sentence.idx;
    // save text if changes were made
    const text = replaceWithLineBreaks(this.state.text);
    const initialText = this.props.sentence.form;
    if (text !== initialText) {
      this.setState({ isSubmitting: true });

      dispatch(submitEditSentence(idx, { text }))
        .then(() => {
          this.exitEditMode();
          this.setState({ isSubmitting: false });
        }).catch(() => {
          this.setState({ isSubmitting: false });
        });
    } else {
      this.exitEditMode();
    }
  },

  // Used by OnClickOutside
  handleClickOutside() {
    // if textarea has text show 'confirm delete' modal
    if (this.state.isUnsavedComment) {
      return this.openConfirmDeleteModal()
    }

    if (!this.state.introJsObject && !this.state.textChanged && !this.state.isConfirmDeleteOpen) { //disable click outside for the introJS and 'confirm delete' modal
      this.onSubmit();
      this.onClose();
    }
  },

  onClickCloseBtn() {
    // if textarea has text show 'confirm delete' modal
    if (this.state.isUnsavedComment) {
      return this.openConfirmDeleteModal();
    }

    // don't save
    this.onClose();
  },

  onPendingTextEditAreaChange(text) {
    this.setState({
      text,
      textChanged: true
    });
  },

  onAcceptChange() {
    const { sentence, dispatch } = this.props;
    const idx = sentence.idx;
    dispatch(acceptChange(idx));
    this.props.disableEditMode();
  },

  onRejectChange() {
    const { sentence, dispatch } = this.props;
    const idx = sentence.idx;

    dispatch(rejectChange(idx));
    this.props.disableEditMode();
  },

  openConfirmDeleteModal() {
    this.setState({ isConfirmDeleteOpen: true });
  },

  closeConfirmDeleteModal() {
    this.setState({ isConfirmDeleteOpen: false });
  },

  handleCommentBoxChange(value) {
    this.setState({ isUnsavedComment: value ? true : false });
  },

  render() {
    const user = this.props.user.toJS();
    const sentence = this.props.sentence;

    const hasUnapprovedRevision = !!sentence.latestRevision;

    const lock = sentence.lock;
    const isLockedOut = lock !== null && lock.owner.username !== user.username;

    const text = replaceWithLineBreaks(this.state.text);

    const textPending = !!text && text !== sentence.form;
    const textDeletePending = text === '';

    const boxStyle = classNames(
      'beagle-editor-box', {
        'condensed': this.props.isCondensed,
        'regular': !this.props.isCondensed,
        'is-clause-table': this.props.isClauseTable,
      }
    );

    const closeTooltip = this.state.editMode ? (
      <Tooltip id={uuidV4()}>
        <strong>Cancel edits</strong>
      </Tooltip>
    ) : null;

    const closeBtn = (
      <div className="close-btn" onClick={this.onClickCloseBtn}>
        <i className="fa fa-times" />
      </div>
    );

    const closeBtnWithTooltip = closeTooltip ? (
      <OverlayTrigger placement="top" overlay={closeTooltip}>
        {closeBtn}
      </OverlayTrigger>
    ) : closeBtn;

    // computes a small string that is kind of unique for the tags and suggested
    // tags that are on the sentence object so that the TagTools component
    // re-renders when tags change
    const tagsHash = 'tags-' +
      '?' + (sentence.tags || []).map(t => t[0]).join('') +
      '!' + (sentence.suggested_tags || []).map(t => t[0]).join('');

    return (
      <div className={boxStyle} id="eb-step1" ref="editorBox">
        {closeBtnWithTooltip}
        <ConfirmDeleteModal
          show={this.state.isConfirmDeleteOpen}
          title="Are you sure?"
          content="Your comment will be deleted"
          onHide={this.closeConfirmDeleteModal}
          onSubmit={this.onClose} />
        <div className="editor-contents">
          <div className="textarea-contents" id="eb-step2">
            <ClauseView
              sentence={sentence}
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
              username={user.username || ''}
              sentence={sentence} />
            <RevisionControls
              pending={textPending}
              deletePending={textDeletePending}
              unapproved={hasUnapprovedRevision}
              acceptChange={this.onAcceptChange}
              rejectChange={this.onRejectChange}
              submitRevision={this.onSubmit}
              isSubmitting={this.state.isSubmitting}
            />
          </div>
          <TagTools
            key={tagsHash}
            user={user}
            sentence={sentence} />
          <div className="control-panel">
            <CommentPanel sentence={sentence} user={user} onChange={this.handleCommentBoxChange} />
          </div>
        </div>
      </div>
    );
  }

}));


const mapStateToProps = (state) => {
  return {
    user: state.user,
    lock: state.lock
  }
};

// Need to acces this refs
export default connect(mapStateToProps, null, null, { withRef: true })(EditorBoxComponent)
