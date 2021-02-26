var React = require('react');
var Reflux = require('reflux');
import _ from 'lodash';
var CSV = require('comma-separated-values');
var downloadCSV = require('utils/downloadCSV');
var Tooltip = require('react-bootstrap/lib/Tooltip');
var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');
var ToggleBtn = require('report/components/ToggleBtn');
var ClauseTable = require('./ClauseTable/ClauseTable');
var AgreementEditor = require('report/components/AgreementEditor');
var UserStore = require('common/stores/UserStore');
var ReportStore = require('report/stores/ReportStore');

var Spinner = require('report/components/Spinner');
var { formatDate } = require('report/utils');

var ClauseTableView = React.createClass({

  mixins: [
    Reflux.connect(ReportStore, "annotations"),
    Reflux.connect(UserStore, 'user')
  ],

  downloadCSV(sentences) {
    downloadCSV(
      sentences,
      this.state.annotations.title,
      this.state.annotations.created,
      this.state.user,
      this.state.annotations.analysis.parties
    );
  },

  componentDidMount() {
    this.introJsClauseTableEvoke();
  },

  //Starts the clause table overlay intro wizard
  introJsClauseTableEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof introJs !== 'undefined' && !INTROJS_STEPS_CLAUSE_TABLE_DONE) {
      var intro = introJs();
      intro.setOptions(INTROJS_STEPS_CLAUSE_TABLE);
      intro.start();
      INTROJS_STEPS_CLAUSE_TABLE_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  render() {

    var analysis = this.state.annotations.analysis || null;
    if (!analysis || !analysis.sentences.length !== 0) {
      return <Spinner/>;
    }

    return (
      <div>
        <ClauseTable
          analysis={analysis}
          downloadCSV={this.downloadCSV}
        />
      </div>
    );
  }

});


module.exports = ClauseTableView;
