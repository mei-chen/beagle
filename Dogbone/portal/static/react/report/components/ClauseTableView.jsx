import React from 'react';
import { connect } from 'react-redux';

// App
import downloadCSV from 'utils/downloadCSV';
import ClauseTable from './ClauseTable/ClauseTable';
import Spinner from './Spinner';
import _ from 'lodash';
import constants from '../constants';
import { sendUserEventToServer } from '../redux/modules/userEventsStatistics';

const userEvents = constants.UserEvents;

const ClauseTableView = React.createClass({
  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(sendUserEventToServer(userEvents.OPEN_CLAUSE_VIEW))
    this.introJsClauseTableEvoke();
  },

  downloadCSV(sentences) {
    const { report, user } = this.props;
    const analysis = report.get('analysis').toJS();

    downloadCSV(
      sentences,
      report.get('title'),
      report.get('created'),
      user.toJS(),
      analysis.parties
    );
  },

  //Starts the clause table overlay intro wizard
  introJsClauseTableEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof window.introJs !== 'undefined' && !window.INTROJS_STEPS_CLAUSE_TABLE_DONE) {
      var intro = window.introJs();
      intro.setOptions(window.INTROJS_STEPS_CLAUSE_TABLE);
      intro.start();
      window.INTROJS_STEPS_CLAUSE_TABLE_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  getDocumentAnnotations() {
    var allAnnotations = [];
    var temp = [];
    //pluck out all annotation arrays
    var annotations = _.map(this.props.report.get('analysis').toJS().sentences, 'annotations');
    //filter out the empty annotations arrays
    annotations = _.filter(annotations, a => { return a; });
    //flatten array of arrays
    annotations = allAnnotations.concat.apply(allAnnotations, annotations);
    //dedup array of annotation objects
    annotations = annotations.filter(a => {
      //if we've not yet encountered a label it is unique,
      if (!(temp.indexOf(a.label) > -1)) {
        //add the annotation label to a temp array of uniques
        temp.push(a.label);
        return true
      //if the label is in the temp array of uniques, it is filtered out.
      } else {
        return false
      }
    });
    return annotations;
  },

  render() {
    const { report } = this.props;
    const analysis = report.get('analysis').toJS();

    if (!(analysis && analysis.sentences.length !== 0)) {
      return <Spinner/>;
    }

    return (
      <div>
        <ClauseTable
          analysis={analysis}
          getDocumentAnnotations={this.getDocumentAnnotations}
          downloadCSV={this.downloadCSV}
        />
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  return {
    report: state.report,
    user: state.user,
    isInitialized: state.report.get('isInitialized')
  }
};

export default connect(mapStateToProps)(ClauseTableView)
