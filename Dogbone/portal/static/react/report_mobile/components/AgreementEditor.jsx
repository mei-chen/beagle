var React = require('react');
var Reflux = require('reflux');
var $ = require('jquery');
import _ from 'lodash';
var invariant = require('invariant');
var classNames = require('classnames');
var PureRenderMixin = React.addons.PureRenderMixin;
var { Navigation, State } = require('react-router');

var Spinner = require('report/components/Spinner');
var Sentence = require('./Sentence');
var LockStore = require('report/stores/LockStore');
var ReportStore = require('report/stores/ReportStore');
var BeaglePropTypes = require('utils/BeaglePropTypes');
var { ReportActions, LockActions } = require('report/actions');

require('./styles/AgreementEditor.scss');


var SentencesView = React.createClass({

  mixins: [PureRenderMixin, Navigation, State],

  propTypes: {
    sentences: React.PropTypes.array.isRequired,
    liabActive: React.PropTypes.bool.isRequired,
    respActive: React.PropTypes.bool.isRequired,
    termActive: React.PropTypes.bool.isRequired,
    refsActive: React.PropTypes.bool.isRequired,
    isModalView: React.PropTypes.bool.isRequired
  },

  getInitialState() {
    return {
      focusedSentenceIdx: null
    };
  },

  getCurrentRouteName() {
    var routes = this.getRoutes();
    invariant(routes.length === 2, "unexpected route path");
    return routes[1].name;
  },

  focusOnSentence(sentenceIdx) {
    this.setState({ focusedSentenceIdx: sentenceIdx });
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
    let callback = () => {
      this.transitionTo(
        this.getCurrentRouteName(),
        this.getParams(), // don't change URL params
        {...this.getQuery(), idx: idx } // update query with `idx`
      );
    };
    this.setState({ focusedSentenceIdx: null }, callback);
  },

  /**
   * disableEditMode
   *
   * Removes the `idx` query param from the URL, thereby disabling edit mode.
   *
   */
  disableEditMode() {
    let { idx, newQuery } = this.getQuery();
    this.transitionTo(
      this.getCurrentRouteName(),
      this.getParams(), // don't change URL params
      newQuery
    );
  },

  render() {
    return (
      <div className="annotation-editor">
        {this.props.sentences.map(sentence => {
          return (
            <Sentence
              isActive
              key={sentence.idx}
              sentence={sentence}
              enableEditMode={() => this.enableEditModeForNewSentence(sentence.idx)}
              disableEditMode={this.disableEditMode}
              focusedSentenceIdx={this.state.focusedSentenceIdx}
              {...this.props}
            />
          );
        })}
      </div>
    );
  },

});


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
      },
      showBackToTop: false
    };
  },

  componentDidMount() {
    this._updateViewportListener = _.throttle(this.updateViewport, 100);
    window.addEventListener('scroll', this._updateViewportListener);
    window.addEventListener('resize', this._updateViewportListener);
    this.updateViewport();
  },

  componentWillUnmount() {
    if (this._updateViewportListener) {
      window.removeEventListener('scroll', this._updateViewportListener);
      window.removeEventListener('resize', this._updateViewportListener);
    }
  },

  updateViewport() {
    let newState = {
      viewport: {
        top: window.pageYOffset,
        height: window.innerHeight
      },
      showBackToTop: window.pageYOffset > 920
    };
    this.setState(newState);

    //reposition the introJs tooltip to scroll with page (if applicable)
    if (!!this.props.introJsObject && !INTROJS_STEPS_EDITOR_BOX_DONE) {
      console.log('tooltip shuffle');
      $('.introjs-tooltip').css({'top' : this.state.viewport.top + 'px'});
    }
  },

  onBackToTopClick() {
    $('body').animate({
      // back to the top son
      scrollTop: 0
    });
  },

  focusSentence(sentenceIdx) {
    this.refs.sentencesView.focusOnSentence(sentenceIdx);
  },

  openEditor(sentenceIdx) {
    this.refs.sentencesView.enableEditModeForSentence(sentenceIdx);
  },

  render() {
    let { analysis, className, ...props } = this.props;

    let parties = {
      you: analysis.parties.you.name,
      them: analysis.parties.them.name,
      both: 'Both'
    };

    let backToTop;
    if (this.state.showBackToTop) {
      backToTop = (
        <div className="back-to-top" onClick={this.onBackToTopClick}>
          Back to top <i className="fa fa-long-arrow-up" />
        </div>
      );
    };

    return (
      <div className={className}>
        <div className="agreement-editor">
          <SentencesView ref="sentencesView"
            sentences={analysis.sentences}
            focusSentence={this.focusSentence}
            {...props}
          />
          {backToTop}
        </div>
      </div>
    );
  }

});


module.exports = AgreementEditor;
