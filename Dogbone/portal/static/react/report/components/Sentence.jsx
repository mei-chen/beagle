import _ from 'lodash';

import React from 'react';
import ReactDOM from 'react-dom';
import { connect } from 'react-redux';
import $ from 'jquery';
import assign from 'object-assign';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import classNames from 'classnames';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

import EditorBox from './EditorBox';
import breakLines from 'utils/insertLineBreaks';
import insertIndents from 'utils/insertIndents';
import groupedTextDiff from 'utils/groupedTextDiff';
import LINEBREAK_MARKER from 'utils/LINEBREAK_MARKER';
import splitExternalReferences from 'utils/splitExternalReferences';
import { submitEditSentence } from 'report/redux/modules/report';
import replaceWithLineBreaks from 'utils/replaceWithLineBreak';

const styles = require('./styles/Sentence.scss');
require('utils/constants.js');


var SentenceComponent = React.createClass({

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
    // Causing bugs
    this.focusEditorBoxIfNeeded();
  },

  componentDidUpdate(oldProps) {
    this.redrawSentenceIfNeeded(oldProps);
    this.focusEditorBoxIfNeeded(oldProps);  // Causing bugs
  },

  forceWebkitRedraw() {
    // thanks http://stackoverflow.com/a/14382251
    var el = ReactDOM.findDOMNode(this);
    var displayMode = $(el).css('display');
    $(el).css('display', 'none').height();
    $(el).css('display', displayMode);
  },

  clearPendingText() {
    this.setState({ pendingText: null });
  },

  onSaveSentenceText() {
    const { dispatch, sentence } = this.props;
    const idx = sentence.idx;
    const text = replaceWithLineBreaks(this.state.pendingText);
    dispatch(submitEditSentence(idx, { text }));
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
    const { focusedSentenceIdx, sentence, editingSentenceIdx } = this.props;
    const { idx } = sentence;
    const isFocused = focusedSentenceIdx === idx;
    const isEditing = editingSentenceIdx === idx;

    const isTransition = (
      focusedSentenceIdx &&
      focusedSentenceIdx !== oldProps.focusedSentenceIdx
    );

    const isEditingTransition = (
      editingSentenceIdx &&
      editingSentenceIdx !== oldProps.editingSentenceIdx
    );

    let currentContainer;
    if (editingSentenceIdx) {
      currentContainer = this.refs.editorBoxContainer;
    } else {
      currentContainer = this.refs[`sentence-${sentence.idx}-view`];
    }

    const isInTransition = (isFocused || isEditing) && (isTransition || isEditingTransition);

    if (currentContainer && isInTransition) {
      // http://stackoverflow.com/questions/34004331/react-es6-how-to-access-child-component-functions-via-refs
      // A bit hacky
      let currentContainerInstance;

      if (currentContainer.getWrappedInstance !== undefined) {
        currentContainerInstance = currentContainer.getWrappedInstance().refs.instance.refs.editorBox;
      } else {
        currentContainerInstance = currentContainer;
      }

      const currentContainerAbsOffsetTop = (
        currentContainerInstance.offsetTop +
        (currentContainerInstance.offsetParent && currentContainerInstance.offsetParent.offsetTop || 0)
      );

      const newScrollTop = currentContainerAbsOffsetTop - screen.height / 6;
      const animProps = { scrollTop: newScrollTop };
      const callback = this.props.onFocusCallback;
      $('html, body').animate(animProps, callback);
    }
  },

  onSentenceClick() {
    this.props.enableEditMode();
    if (!!this.props.introJsObject && !window.INTROJS_STEPS_EDITOR_BOX_DONE) {
      this.props.introJsObject.exit()
    }
  },

  onOverlayClick() {
    this.props.disableEditMode();
  },

  render() {
    const { sentence } = this.props;

    // Test if empty sentence
    if (sentence.form.trim() === '' && !sentence.latestRevision) {
      // this is a new line only. no text to display and no render logic required
      if (sentence.newlines && sentence.newlines > 0) {
        return <div key={sentence.idx} className={styles.linebreak}><br/></div>;
      } else {
        return <span />
      }
    }

    const editingSentenceIdx = this.props.editingSentenceIdx;
    const isEditing = editingSentenceIdx === sentence.idx;
    const noneEditing = editingSentenceIdx === null;
    const otherEditing = !isEditing && !noneEditing;

    if (isEditing) {
      return (
        <EditorBox
          sentence={sentence}
          isCondensed={this.props.isModalView}
          isClauseTable={false}
          disableEditMode={this.props.disableEditMode}
          ref="editorBoxContainer"
        />
      );
    }

    const extRefs = sentence.external_refs || [];
    const hasExternalReferences = extRefs.length > 0;

    const focusedSentenceIdx = this.props.focusedSentenceIdx;
    const isFocused = !isEditing && !otherEditing && (focusedSentenceIdx === sentence.idx);
    const noneFocused = focusedSentenceIdx === null;

    const refsAreEnabled = noneFocused && this.props.refsActive;


    const isDeleted = sentence.deleted === true;
    const isLocked = sentence.lock !== null;

    const sentenceClasses = classNames({
      [styles.sentence]: true,
      'beagle-report-sentence': true,
      'locked': isLocked,
      'deleted': isDeleted,
      'focused': isFocused,
      'ignore-react-onclickoutside': isEditing,
    });

    const textClasses = classNames({
      'sentence-text': true,
      'style-bold': sentence.style ? sentence.style.bold : false,
      'style-underline': sentence.style ? sentence.style.underline : false,
    });

    const deletedColour = 'red';
    const sentenceStyles = {};
    const underlineStyles = {};
    const textStyles = {};

    const { learners } = this.props;
    let colorCode;
    if (sentence.annotations && sentence.annotations.length && learners) {
      learners.map(learner => {
        if (learner.name.toLowerCase() === sentence.annotations[0].label.toLowerCase())
        {
          colorCode=learner.color_code;
        }
      })
    }

    textStyles.background = colorCode;

    if (sentence.style) {
      textStyles.fontSize = (11 + (sentence.style.size || 0)) + 'pt';
    }

    // handle entire sentence deleted styles
    const fontSize = sentence.style ? sentence.style.size : 0;
    assign(sentenceStyles, {
    //linear ecuation for almost perfect spacing between rows
      lineHeight: (26 + (fontSize*1.17 || 0)) + 'px',
    });
    if (isDeleted) {
      assign(sentenceStyles, {
        color: deletedColour,
        textDecoration: 'line-through',
      });
      assign(textStyles, {
        color: deletedColour
      });
    }

    const refClasses = classNames(
      'annotation',
      'refs',
      (refsAreEnabled || isFocused) ? 'active' : null
    );

    // will be an array of nodes.
    // broken up due to line breaks, diff, ext refs...
    let sentenceChildren;

    const hasUnapprovedRevision = (sentence.accepted === false && !!sentence.latestRevision);

    if (hasUnapprovedRevision) {
      const oldText = sentence.latestRevision.form;
      const newText = sentence.form;

      const diff = groupedTextDiff(oldText, newText);

      sentenceChildren = _.flatten(diff.map((part, idx) => {
        const chunkStyle = {
          color: (part.removed) ? deletedColour : (part.added) ? 'blue' : null,
          textDecoration: (part.removed) ? 'line-through' : null,
        };
        const children = [];
        // LINEBREAK_MARKERs were already replaced with '\n' in groupedTextDiff,
        // so there aren't any LINEBREAK_MARKERs in diff's parts
        part.value.split('\n').forEach(splitSubstring => {
          children.push(<span key={`${idx}.span`} style={chunkStyle}>{splitSubstring}</span>);
          children.push(<br key={`${idx}.br`}/>);
        });
        return _.dropRight(children);
      }));
    }
    else if (hasExternalReferences) {
      const strings = splitExternalReferences(sentence);
      sentenceChildren = _.flatten(strings.map(string => {
        const childRefClasses = string.ref === true ? refClasses : null;
        const splitStrings = string.text.split(LINEBREAK_MARKER);
        const nodes = [];
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

    // Split lines on line-breaks
    if (sentence.contains_linebreaks) {
      const splitChildren = [];
      sentenceChildren.forEach(child => {
        splitChildren.push(breakLines(child));
      });
      sentenceChildren = _.flatten(splitChildren);
    }
    // Add indents
    var splitChildren = [];
    sentenceChildren.forEach(child => {
      splitChildren.push(insertIndents(child));
    });
    sentenceChildren = _.flatten(splitChildren);

    let comment;
    const comments = (sentence.comments || []).filter(c => c != null);
    const filteredComments = comments.filter(comm => {
      return comm.author.username !== '@beagle';
    });
    const sortedUniqueCommentorNames = _.sortBy(_.uniq(filteredComments.map(comm => {
      return comm.author.first_name || comm.author.username;
    })));
    const commentorNames = sortedUniqueCommentorNames.map(name => {
      return <li key={name}><strong>{name}</strong></li>;
    });
    const commentorNamesTooltip = <Tooltip id="1"><ul className="tooltip-ul">{commentorNames}</ul></Tooltip>;
    if (sentence.comments) {
      comment = (
        <OverlayTrigger placement="top" overlay={commentorNamesTooltip}>
          <i onClick={this.onSentenceClick} className="fa fa-comment comments"/>
        </OverlayTrigger>
      );
    }

    // Assign a sequential key to every sentence child
    sentenceChildren = sentenceChildren.map((child, idx) => {
      if (child.props) { // is a ReactElement
        const newProps = { ... child.props, key: idx };
        return React.cloneElement(child, newProps);
      } else { // is just a string
        return child;
      }
    });

    // If there is a sentence lock, display the locked users icon
    let lockIcon;
    if (sentence.lock) {
      const lockOwner = sentence.lock.owner;
      const avatarStyle = {
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

    const newlines = [];
    for (let i = 0; i < Math.min(sentence.newlines, 10); i++) {
      newlines.push(<br key={i + 'trail-br'}/>);
    }
    return (
      <span className={sentenceClasses}
            style={sentenceStyles}
            onClick={this.onSentenceClick}
            onMouseOver={this.props.onSentenceHover}
            onMouseOut={this.props.offSentenceHover}
            ref={`sentence-${sentence.idx}-view`}>
        <span style={underlineStyles}>
          <span className={textClasses} style={textStyles}>
            {sentenceChildren}
          </span>
        </span>
        {comment}
        {lockIcon}
        {newlines}
      </span>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    user: state.user
  }
};

export default connect(mapStateToProps)(SentenceComponent)
