import React from 'react';
import _ from 'lodash';
import classNames from 'classnames';

import Widget from './Widget';
import Spinner from './Spinner';

require('./styles/ResponsibilitiesWidget.scss');


const Party = React.createClass({

  render() {
    var both = this.props.both;
    var resps = this.props.resps || [];
    var width = this.props.width;

    var partyLineClasses = classNames(
      'resp-line',
      this.props.className
    );

    var partyLineWidth = (resps.length / width) * 100 + '%';
    var bothLineWidth = (resps.length / width) + (both.length / width) * 100 + '%';

    var partyLine;
    if (resps.length > 0) {
      partyLine = (
        <div className={partyLineClasses}
          style={{ width: partyLineWidth }}/>
      );
    }

    var bothLine;
    if (both.length > 0) {
      bothLine = (
        <div className="resp-line both"
          style={{
            width: bothLineWidth,
            left: partyLineWidth
          }}/>
      );
    }

    return (
      <div className={this.props.className}>
        <div className="text">
          <span className="name">{this.props.partyName}</span>
          <span className="score">{resps.length + both.length}</span>
        </div>
        <div className="resp-bg">
          {bothLine}
          {partyLine}
        </div>
      </div>
    );
  }

});


var ResponsibilitiesWidget = React.createClass({

  SCALE: 1.15,

  render() {
    const isLoaded = this.props.analysis && this.props.analysis.sentences.length !== 0;

    var body;
    if (isLoaded) {
      var parties = this.props.analysis.parties;
      var sentences = _.filter(this.props.analysis.sentences, function(s) {
        return s.annotations && s.annotations.length > 0;
      });
      var responsibilities = _.filter(sentences, function(s) {
        return _.find(s.annotations, { label: 'RESPONSIBILITY' });
      });
      var yours = _.filter(responsibilities, function(s) {
        return _.find(s.annotations, { party: 'you' });
      });
      var theirs = _.filter(responsibilities, function(s) {
        return _.find(s.annotations, { party: 'them' });
      });
      var both = _.filter(responsibilities, function(s) {
        return _.find(s.annotations, { party: 'both' });
      });
      var width = Math.max(yours.length + both.length,
                           theirs.length + both.length) * this.SCALE;
      body = (
        <div id="responsibilities">
          <Party
            className="partya"
            partyName={parties.you.name}
            resps={yours}
            both={both}
            width={width}/>
          <Party
            className="partyb"
            partyName={parties.them.name}
            resps={theirs}
            both={both}
            width={width}/>
          <Party
            className="both"
            partyName="Both"
            both={both}
            width={width}/>
        </div>
      );
    } else {
      body = <Spinner />;
    }
    return <Widget title="Responsibilities" className="Responsibilities"> {body} </Widget>;
  }

});


module.exports = ResponsibilitiesWidget;
