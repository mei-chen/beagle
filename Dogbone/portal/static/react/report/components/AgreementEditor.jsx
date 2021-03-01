import _ from 'lodash';

import React from 'react';
import $ from 'jquery';
import { connect } from 'react-redux';

// App
import Sentence from './Sentence';
import {
  setFocusSentence,
  removeFocusSentence
} from 'report/redux/modules/app';

require('./styles/AgreementEditor.scss');


const SentencesViewComponent = React.createClass({
  propTypes: {
    sentences: React.PropTypes.array.isRequired,
    liabActive: React.PropTypes.bool.isRequired,
    respActive: React.PropTypes.bool.isRequired,
    termActive: React.PropTypes.bool.isRequired,
    refsActive: React.PropTypes.bool.isRequired,
    isModalView: React.PropTypes.bool.isRequired
  },

  contextTypes: {
    router: React.PropTypes.object.isRequired
  },

  // mixins: [PureRenderMixin, Navigation, State],

  getInitialState() {
    return {
      focusedSentenceIdx: null
    };
  },

  getCurrentRouteName() {
    return this.context.router.location.pathname;
  },

  focusOnSentence(idx) {
    const { dispatch } = this.props;
    dispatch(setFocusSentence(idx));
  },

  /**
   * enableEditModeForNewSentence
   *
   * Appends the provided `idx` to the URL query string, thereby opening the
   * editor box for the sentence with given `idx`.
   *
   * @param {int} idx sentence idx to transition to
   */
  enableEditModeForNewSentence(idx) {
    const { dispatch } = this.props;
    dispatch(removeFocusSentence(idx));

    this.context.router.push({
      ... this.context.router.location,
      query: { ... this.context.router.location.query, idx: idx } // update query with `idx`
    });
  },

  /**
   * disableEditMode
   *
   * Removes the `idx` query param from the URL, thereby disabling edit mode.
   *
   */
  disableEditMode() {
    const { dispatch } = this.props;
    const query = this.context.router.location.query;
    dispatch(removeFocusSentence(query.idx));
    query.idx = undefined;

    this.context.router.push({
      ... this.context.router.location,
      query
    });
  },

  render() {
    const { app } = this.props;
    const focusedSentenceIdx = app.get('focusedSentenceIdx');
    const sentHoverFn = function(idx, sentenceHoverFunction) {
      if (sentenceHoverFunction != undefined) {
        return () => sentenceHoverFunction(idx);
      }
    }
    const sentHoverOffFn = function(idx, sentenceHoverOffFunction) {
      if (sentenceHoverOffFunction != undefined) {
        return () => sentenceHoverOffFunction(idx);
      }
    }

    return (
      <div className="annotation-editor">
        {this.props.sentences.map(sentence => {
          return (
            <Sentence
              isActive
              learners={this.props.learners}
              onSentenceHover={sentHoverFn(sentence.idx, this.props.sentenceHoverFn)}
              offSentenceHover={sentHoverOffFn(sentence.idx, this.props.sentenceHoverOffFn)}
              key={sentence.idx}
              sentence={sentence}
              enableEditMode={() => this.enableEditModeForNewSentence(sentence.idx)}
              disableEditMode={this.disableEditMode}
              focusedSentenceIdx={focusedSentenceIdx}
              {...this.props}
            />
          );
        })}
      </div>
    );
  },
});

const mapSentencesViewComponentStateToProps = (state) => {
  return {
    app: state.app,
  }
};

const SentencesView = connect(mapSentencesViewComponentStateToProps)(SentencesViewComponent)

var AgreementEditor = React.createClass({

  propTypes: {
    analysis: React.PropTypes.object.isRequired
  },

  getDefaultProps() {
    return {
      liabActive: true,
      respActive: true,
      termActive: true,
      refsActive: true,
    };
  },

  getInitialState() {
    return {
      viewport: {
        top: 0,
        height: 0
      }
    };
  },

  componentDidMount() {
    this.initializeUpdateViewPort();
  },

  componentWillUnmount() {
    if (this._updateViewportListener) {
      window.removeEventListener('scroll', this._updateViewportListener);
      window.removeEventListener('resize', this._updateViewportListener);
    }
  },

  // Causing display bugs
  initializeUpdateViewPort() {
    this._updateViewportListener = _.throttle(this.updateViewport, 100);
    window.addEventListener('scroll', this._updateViewportListener);
    window.addEventListener('resize', this._updateViewportListener);
    this.updateViewport();
  },

  updateViewport() {
    let newState = {
      viewport: {
        top: window.pageYOffset,
        height: window.innerHeight
      }

    };
    this.setState(newState);

    //reposition the introJs tooltip to scroll with page (if applicable)
    if (!!this.props.introJsObject && !window.INTROJS_STEPS_EDITOR_BOX_DONE) {
      $('.introjs-tooltip').css({ 'top' : this.state.viewport.top + 'px' });
    }
  },

  focusSentence(sentenceIdx) {
    this.refs.sentencesView.focusOnSentence(sentenceIdx);
  },

  openEditor(sentenceIdx) {
    this.refs.sentencesView.enableEditModeForSentence(sentenceIdx);
  },

  render() {
    let { analysis, className, ...props } = this.props;

    return (
      <div className={className}>
        <div className="agreement-editor">
          <SentencesView
            ref="sentencesView"
            sentences={analysis.sentences}
            focusSentence={this.focusSentence}
            {...props}
          />
        </div>
      </div>
    );
  }
});

export default connect()(AgreementEditor)
