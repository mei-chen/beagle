import _ from 'lodash';

import React from 'react';
import $ from 'jquery';
import assign from 'object-assign';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import classNames from 'classnames';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import { connect } from 'react-redux';
import uuidV4 from 'uuid/v4';

// App
import Spinner from './Spinner';
import ListOfTerms from './ListOfTerms';
import AgreementEditor from './AgreementEditor';
import {
  setFocusSentence
} from 'report/redux/modules/app';
import constants from '../constants';
import { sendUserEventToServer } from '../redux/modules/userEventsStatistics';

require('./styles/ContextView.scss');

const userEvents = constants.UserEvents;

function coalesce(a, b) {
  return a == null ? b : a;
}

/**
 * bcrToObj
 *
 * Converts a ClientRect to a plain JS object
 *
 * @param {ClientRect} bcr
 */
function bcrToObj(bcr) {
  return {
    bottom: bcr.bottom,
    height: bcr.height || 0,
    left: bcr.left,
    right: bcr.right,
    top: bcr.top,
    width: bcr.width
  }
}


/**
 * getBoundingRect
 *
 * Reference:
 * https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect
 * https://msdn.microsoft.com/en-us/library/hh781509(v=vs.85).aspx
 *
 * @param {DOMNode} node
 */
function getBoundingRect(node) {
  const bcr = bcrToObj(node.getBoundingClientRect());
  const offset = $(node).offset();
  const styles = window.getComputedStyle(node);
  bcr.top = offset.top;
  bcr.left = offset.left;
  bcr.height = parseInt(styles.height || 0, 10);
  bcr.bottom = document.body.scrollHeight - bcr.top - bcr.height;
  return bcr
}


class TrackChangeButton extends React.Component {

  render() {
    let { prev, next, isActive, ...props } = this.props;

    let buttonClasses = classNames(
      'track-changes-btn', {
        prev, next, isActive
      }
    );

    let iconClasses = classNames(
      'fa', {
        'fa-arrow-left': prev,
        'fa-arrow-right': next
      }
    );

    let tooltip = (
      <Tooltip id={uuidV4()}>
        {prev ? 'Previous track change' : 'Next track change'}
      </Tooltip>
    );

    return (
      <OverlayTrigger placement="top" overlay={tooltip}>
        <button className={buttonClasses} {...props}>
          <i className={iconClasses} />
        </button>
      </OverlayTrigger>
    );
  }

}


const ContextView = React.createClass({

  propTypes: {
    analysis: React.PropTypes.object.isRequired
  },

  contextTypes: {
    router: React.PropTypes.object.isRequired
  },

  getInitialState() {
    return {
      lastFocused: null,
      openSection: this.props.query.s || null,
      leftBCR: {},
      rightBCR: {},
      introJsObject: null
    };
  },

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(sendUserEventToServer(userEvents.OPEN_CONTEXT_VIEW))
    this.updateBCRs();
    this._resizeListener = _.throttle(this.updateBCRs, 10, {
      leading: true, trailing: true
    });
    this._scrollListener = _.throttle(this.updateScroll, 10);
    window.addEventListener('resize', this._resizeListener);
    window.addEventListener('scroll', this._scrollListener);

    //envoke the introJs (function will decide if applicable)
    this.introJsContextViewEvoke();
  },

  componentDidUpdate(oldProps) {
    if (!!oldProps.query.idx && this.props.query.idx == null) {
      this.updateBCRs();
    }
  },

  componentWillUnmount() {
    window.removeEventListener('resize', this._resizeListener);
    window.removeEventListener('scroll', this._scrollListener);
  },

  focusSentence(sentenceIdx) {
    const { dispatch } = this.props;

    this.setState({ lastFocused: sentenceIdx }, () => {
      dispatch(setFocusSentence(sentenceIdx));
    });
  },

  getCurrentRouteName() {
    return this.context.router.location.pathname;
  },

  /**
   * openSection
   *
   * Opens the section with the given section string
   * In the URL query string, the param `s` is for `section`
   *
   * @param {string} section a string like "liabilities", "responsibilities"...
   */
  openSection(section) {
    // if clicked on the currently open section, toggle it off
    const newOpenSection = (section !== this.state.openSection) ? section : null;

    // this object is will be the new state
    const stateChange = {
      openSection: newOpenSection
    };

    // will be invoked after successful `setState`
    const updateQueryString = () => {
      const query = this.props.query;
      let newQuery;
      if (newOpenSection) {
        newQuery = assign(query, { s: newOpenSection });
      } else {
        newQuery = assign({}, query); // clone the query obj
        delete newQuery['s']; // delete the `s` key if exists
      }
      this.context.router.replace({
        ... this.context.router.location,
        query: newQuery // new query object (the `s` param)
      });
    };
    // update state, then invoke callback to update URL query string
    this.setState(stateChange, () => {
      updateQueryString();
      this.updateBCRs();
    });
  },

  hasTrackChanges() {
    const { analysis } = this.props;
    const sentences = analysis ? analysis.sentences : [];
    // get first sentence which has a change. if none exist, returns nothing
    const changed = _.find(sentences, { accepted: false });
    return !!changed; // cast the object|nothing to a boolean
  },

  getChangedSentenceIDs() {
    const { analysis } = this.props;
    const sentences = analysis ? analysis.sentences : [];
    // get all of the sentences which shall be highlighted as a change
    const changedSentences = sentences.filter(s => s.accepted === false);
    // pluck out the index of each changed sentence for the returned array
    const changedSentenceIDs = _.map(changedSentences, 'idx');
    return changedSentenceIDs;
  },

  prevTrackChange() {
    const focusedID = this.state.lastFocused || 0;
    const changedIDs = this.getChangedSentenceIDs();
    const earlierIDs = changedIDs.filter(id => id < focusedID);
    const prevID = coalesce(_.last(earlierIDs), _.last(changedIDs));
    this.focusSentence(prevID);
  },

  nextTrackChange() {
    const focusedID = this.state.lastFocused || 0;
    const changedIDs = this.getChangedSentenceIDs();
    const laterIDs = changedIDs.filter(id => id > focusedID);
    const nextID = coalesce(_.first(laterIDs), _.first(changedIDs));
    this.focusSentence(nextID);
  },

  /**
   * updateBCRs
   *
   * Gets the DOM nodes for the left and right sections of the ContextView, gets
   * each's bounding client rect, and caches them to the component state.
   *
   * Uses jQuery's `offset` to compute an accurate 'top' value.
   * `getBoundingClientRect` was returning negative values for some scroll
   * positions, for reasons I don't really get...
   *
   * One alternative could be to reimplement the logic that computes the offset
   * https://github.com/jquery/jquery/blob/0e4477c6/src/offset.js#L109-L110
   *
   */
  updateBCRs() {
    const state = {};
    const left = this.refs.leftSection;
    const right = this.refs.rightSection;

    if (left) {
      state.leftBCR = getBoundingRect(left);
    }
    if (right) {
      state.rightBCR = getBoundingRect(right);
    }
    this.setState(state);
  },

  updateScroll() {
    let scrollY = window.scrollY;
    this.setState({ scrollY }, () => {
      if (scrollY === 0) {
        this.updateBCRs();
      }
    });
  },

  //Starts the context view overlay intro wizard
  introJsContextViewEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    //skip the introjs if the user is directed right to a clause (idx in Query String NOT null)
    if (!this.props.query.idx && typeof window.introJs !== 'undefined' && typeof window.INTROJS_STEPS_CONTEXT_VIEW_DONE !== 'undefined' && !window.INTROJS_STEPS_CONTEXT_VIEW_DONE) {
      const intro = window.introJs();
      intro.setOptions(window.INTROJS_STEPS_CONTEXT_VIEW);
      intro.oncomplete(this.removeIntroJsState);
      intro.onexit(this.removeIntroJsState);
      intro.start();
      this.setState({ introJsObject : intro }); //hang onto the wizard object as the state.
      window.INTROJS_STEPS_CONTEXT_VIEW_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  //Housekeeping: clear away the introJs object state varible when done with it.
  removeIntroJsState() {
    this.setState({ introJsObject : null });
  },

  render() {
    const analysis = this.props.analysis;
    const liabActive = this.state.openSection === 'Liabilities';
    const respActive = this.state.openSection === 'Responsibilities';
    const termActive = this.state.openSection === 'Terminations';
    const refsActive = this.state.openSection === 'references';
    const hasTrackChanges = this.hasTrackChanges();

    const queryIdx = this.props.query.idx
    const idx = queryIdx !== undefined ? parseInt(queryIdx, 10) : null;
    const { leftBCR, rightBCR } = this.state;
    const screenBottom = window.innerHeight + this.state.scrollY;

    // compute the list of terms box screen position
    let topOffset = 50;
    let listOfTermsStickyParentStyles = {
      position: 'fixed',
      width: leftBCR.width || 0,
      top: Math.max((leftBCR.top || 0) - (this.state.scrollY || 0), topOffset),
    };

    const parentTop = listOfTermsStickyParentStyles.top || 0;
    const listOfTermsBottom = Math.max(0, (screenBottom || 0) - (leftBCR.top || 0) - (leftBCR.height || 0));

    // compute styles for the scrolling container
    const listOfTermsScrollingStyles = {
      position: 'absolute',
      overflow: 'scroll',
      width: 'inherit',
      height: window.innerHeight - listOfTermsBottom - parentTop - 50,
      paddingTop:'50px'
    };

    let trackChanges;
    if (hasTrackChanges) {
      // compute the track changes screen position
      let trackChangeStyles = {
        position: 'fixed',
        left: rightBCR.left || 0,
        right: (window.innerWidth - rightBCR.right) || 0,
        bottom: Math.max(0, screenBottom - rightBCR.top - rightBCR.height) || 0,
      };

      trackChanges = (
        <div className="track-changes" style={trackChangeStyles}>
          <TrackChangeButton
            prev
            onClick={this.prevTrackChange}
            isActive={hasTrackChanges} />
          <i className="fa fa-pen-square" />
          <TrackChangeButton
            next
            onClick={this.nextTrackChange}
            isActive={hasTrackChanges} />
        </div>
      );
    }

    return (
      <div className="beagle-context-view">
        <div className="center-content">
          <section ref="leftSection">
            <div style={listOfTermsStickyParentStyles}>
              <div style={listOfTermsScrollingStyles}>
                <ListOfTerms
                  className="dialog-section list-of-terms"
                  openSection={this.state.openSection}
                  focusSentence={this.focusSentence}
                  changeOpenSection={this.openSection}
                  introJsObject={this.state.introJsObject}
                />
              </div>
            </div>
          </section>
          <section ref="rightSection" id="cv-step1" className="beagle-context-view-text">
            {trackChanges}
            <AgreementEditor ref="agreementEditor"
              analysis={analysis}
              className="dialog-section ktext hl-contract"
              respActive={respActive}
              liabActive={liabActive}
              termActive={termActive}
              refsActive={refsActive}
              isModalView={true}
              onFocusCallback={this.updateBCRs}
              editingSentenceIdx={idx}
              introJsObject={this.state.introJsObject}
            />
          </section>
        </div>
      </div>
    );
  }
});

const ContextViewContainer = React.createClass({
  render() {
    const { report } = this.props;
    const analysis = report.get('analysis').toJS();

    if (!(analysis && analysis.sentences.length !== 0)) {
      return <Spinner />;
    } else {
      // this.props contains ReactRouter params that are useful
      return (
        <ContextView
          analysis={analysis}
          query={this.props.location.query}
          {...this.props}
        />
      );
    }
  }
});

const mapStateToProps = (state) => {
  return {
    report: state.report,
    isInitialized: state.report.get('isInitialized')
  }
};

export default connect(mapStateToProps)(ContextViewContainer)
