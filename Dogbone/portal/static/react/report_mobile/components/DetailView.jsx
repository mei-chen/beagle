import _ from 'lodash';

var React = require('react');
var Reflux = require('reflux');
var Tooltip = require('react-bootstrap/lib/Tooltip');
var classNames = require('classnames');
var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');

var Spinner = require('report/components/Spinner');
var ToggleBtn = require('report/components/ToggleBtn');
var AgreementEditor = require('./AgreementEditor');
var UserStore = require('common/stores/UserStore');
var ReportStore = require('report/stores/ReportStore');

require('./styles/DetailView.scss');

/* thanks to http://stackoverflow.com/a/20873568 */


var DetailView = React.createClass({

  mixins: [Reflux.connect(ReportStore, "analysis")],

  componentDidMount() {
    this.introJsDetailViewEvoke()
  },

  //Starts the editor box overlay intro wizard
  introJsDetailViewEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof introJs !== 'undefined' && !INTROJS_STEPS_DETAIL_VIEW_DONE) {
      var intro = introJs();
      intro.setOptions(INTROJS_STEPS_DETAIL_VIEW);
      intro.start();
      INTROJS_STEPS_DETAIL_VIEW_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  getInitialState() {
    return {
      liab: true,
      resp: true,
      term: true,
      refs: true
    };
  },

  toggleLabel(labelGroup) {
    var toggle = {}; // blank object
    // e.g.: liab = !this.state.liab
    toggle[labelGroup] = !this.state[labelGroup];
    this.setState(toggle);
  },

  render() {
    let analysis = this.state.analysis || null;
    if (_.isEmpty(analysis)) {
      return <Spinner/>;
    }

    var queryIdx = this.props.query.idx;
    var idx = queryIdx !== undefined ? parseInt(queryIdx, 10) : null;

    return (
      <div className="beagle-detail-view">
        <AgreementEditor
          analysis={analysis.analysis}
          liabActive={this.state.liab}
          respActive={this.state.resp}
          termActive={this.state.term}
          refsActive={this.state.refs}
          isModalView={false}
          editingSentenceIdx={idx}
        />
      </div>
    );
  }

});


module.exports = DetailView;
