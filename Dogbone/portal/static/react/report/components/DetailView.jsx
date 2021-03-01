import React from 'react';
import { connect } from 'react-redux';

import Spinner from './Spinner';
import AgreementEditor from './AgreementEditor';
import Infobar from 'report/components/Infobar';
import constants from '../constants';
import { sendUserEventToServer } from '../redux/modules/userEventsStatistics';

require('./styles/DetailView.scss');

const userEvents = constants.UserEvents;

/* thanks to http://stackoverflow.com/a/20873568 */
const DetailViewComponent = React.createClass({

  contextTypes: {
    router: React.PropTypes.object.isRequired
  },

  getInitialState() {
    return {
      liab: true,
      resp: true,
      term: true,
      refs: true
    };
  },

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(sendUserEventToServer(userEvents.OPEN_DETAIL_VIEW))
    this.introJsDetailViewEvoke()
  },

  //Starts the editor box overlay intro wizard
  introJsDetailViewEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof window.introJs !== 'undefined' && !window.INTROJS_STEPS_DETAIL_VIEW_DONE) {
      var intro = window.introJs();
      intro.setOptions(window.INTROJS_STEPS_DETAIL_VIEW);
      intro.start();
      window.INTROJS_STEPS_DETAIL_VIEW_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  toggleLabel(labelGroup) {
    var toggle = {}; // blank object
    // e.g.: liab = !this.state.liab
    toggle[labelGroup] = !this.state[labelGroup];
    this.setState(toggle);
  },

  sentenceHover(sentenceId) {
    const { report } = this.props;
    const analysis = report.get('analysis').toJS();

    var tags = analysis.sentences[sentenceId].annotations;
    this.setState(
      { sentHoverTags: tags }
    );
  },

  senteceHoverOff() {
    var tags = null;
    this.setState(
      { sentHoverTags: tags }
    );
  },

  render() {
    const { report, areLearnersInitialized } = this.props;
    const analysis = report.get('analysis').toJS();
    const learners = report.get('learners').toJS();

    if (!(analysis && analysis.sentences.length !== 0) || !areLearnersInitialized) {
      return <Spinner/>;
    }

    var queryIdx = this.context.router.location.query.idx;
    var idx = queryIdx ? parseInt(queryIdx, 10) : null;
    return (

      <div className="beagle-detail-view">
        <AgreementEditor
          learners={learners}
          analysis={analysis}
          liabActive={this.state.liab}
          respActive={this.state.resp}
          termActive={this.state.term}
          refsActive={this.state.refs}
          sentenceHoverFn={this.sentenceHover}
          sentenceHoverOffFn={this.senteceHoverOff}
          isModalView={false}
          editingSentenceIdx={idx}
        />

        <Infobar
          learners={learners}
          tags={this.state.sentHoverTags}
          partyMembers={analysis.parties}
        />
      </div>
    );
  }

});


const mapStateToProps = (state) => {
  return {
    report: state.report,
    isInitialized: state.report.get('isInitialized'),
    areLearnersInitialized: state.report.get('areLearnersInitialized')
  }
};

export default connect(mapStateToProps)(DetailViewComponent)
