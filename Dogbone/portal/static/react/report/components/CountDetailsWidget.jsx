import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';

// App
import insertIndents from 'utils/insertIndents';
import LINEBREAK_MARKER from 'utils/LINEBREAK_MARKER';


import Widget from './Widget';
import Spinner from './Spinner';
import {
  getFromServer
} from 'report/redux/modules/clausestatistic';
require('./styles/CountDetailsWidget.scss');

// ClausesStatistic graph component
// const ClausesStatisticsStore = require('../stores/ClausesStatisticsStore');
// const { ClausesStatisticsActions } = require('../actions');

const ClauseCount = React.createClass({
  render() {
    var clauses = this.props.clauses;
    var count = clauses.length;
    var plural = count == 1 ? '' : 's';

    return (
      <div className="clause-count">
          <span className="count">{count}</span>
          <span className="text">clause{plural}</span>
      </div>
    );
  }
});


const ClauseList = React.createClass({

  render() {
    var clauses = this.props.clauses;
    var content;
    if (clauses) {
      content = clauses.map(item => {
        const splitText = item.form.split(LINEBREAK_MARKER).filter(t => !!t.trim());
        var nodes = [];
        splitText.forEach((str, idx) => {
          nodes.push(<span key={`${idx}.span`}>{insertIndents(str)}</span>);
          nodes.push(<br key={`${idx}.br`}/>);
        });
        const sentenceChildren = _.dropRight(nodes);
        return (
          <div className="clause-item" key={item.uuid}>
            { sentenceChildren }
          </div>
        );
      });
    }

    return (
      <div className="clause-list">
        <div className="scroll-container">
          {content}
        </div>
        <div className="bottom-fade-overlay" />
      </div>
    );
  }
});

const ClausesStatisticComponent = React.createClass({
  getInitialState() {
    return ({ statistics: null });
  },

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(getFromServer());

    // this.unsub = ClausesStatisticsStore.listen(this.update);
    // ClausesStatisticsActions.getData();
  },

  update(storeData) {
    this.setState({ statistics: storeData });
  },

  countWords(clause) {
    var words = clause.form.split(/\s+/);
    return words.length;
  },

  render() {
    if (this.state.statistics && this.props.clauses.length > 0) {
      var clauses = this.props.clauses;
      var wcounts = clauses.map(this.countWords);
      var wavg = _.sum(wcounts) / wcounts.length;
      var wstat = this.state.statistics[this.props.tag].avg_word_count;

      var deviation = Math.min((wavg - wstat) / 40.0, 1.0);

      var dv_bar_left = 74 * Math.min(1, 1 + deviation);
      var dv_bar_width = Math.abs(74 * deviation);
      var dv_description;
      var plural = (clauses.length > 1) ? 's' : '';

      if (deviation < 0) {
        dv_description = 'Shorter clause' + plural + ' than average'
      } else {
        dv_description = 'Longer clause' + plural + ' than average'
      }

      return (
        <div className="clause-stats">
          <div className="stats-dial">
            <div className="stats-scale">
              <div className="deviation-bar" style={{ left: dv_bar_left, width: dv_bar_width }} />
              <div className="scale-middle" />
            </div>
          </div>
          <span className="dv-description">{dv_description}</span>
        </div>
      );
    } else {
      return (
        <div className="clause-stats" />
      );
    }
  }
});

const mapClausesStatisticComponentStateToProps = (state) => {
  return {
    clausestatistic: state.clausestatistic
  }
};

const ClausesStatistic = connect(mapClausesStatisticComponentStateToProps)(ClausesStatisticComponent)


const CountDetailsWidget = React.createClass({

  render() {
    const isLoaded = this.props.analysis && this.props.analysis.sentences.length !== 0;

    var body;
    if (isLoaded) {
      const sentences = _.filter(this.props.analysis.sentences, s => s.annotations && s.annotations.length > 0);
      const clauses = _.filter(sentences, s => _.map(s.annotations, a => a.label.toLowerCase()).indexOf(this.props.tag.toLowerCase()) !== -1);
      body = (
        <div id={this.props.klass}>
          <div className="count-stats-widget-container">
            <ClauseCount clauses={clauses}/>
            <ClausesStatistic clauses={clauses} tag={this.props.tag}/>
          </div>
          <ClauseList clauses={clauses}/>
        </div>
      );
    } else {
      body = <Spinner />;
    }
    return <Widget title={this.props.header} isNDA={true} className={this.props.tag}> {body} </Widget>;
  }

});


module.exports = CountDetailsWidget;
