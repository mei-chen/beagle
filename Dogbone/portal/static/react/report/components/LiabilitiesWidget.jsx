import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import _ from 'lodash';
import Widget from './Widget';
import Spinner from './Spinner';

require('./styles/LiabilitiesWidget.scss');

const HeatmapLib = {

  liabilityPoint(r, party) {
    var x, y; // jscs:disable disallowMultipleVarDecl
    if (party === 'you') {
      x = 250;
    } else if (party === 'them') {
      x = 160;
    } else {
      x = 210;
    }
    if (r.substring(0, 3) === 'ABS') { // ABSOLUTE_X
      y = 40;
    } else if (r.substring(0, 4) === 'PART') { // PARTIAL_X
      y = 60;
    } else if (r.substring(0, 4) === 'COND') { // CONDITIONAL_X
      y = 90;
    } else if (r.substring(0, 2) === 'NO') { // NO_X
      y = 110;
    } else { // doesn't match anything
      x = 0;
      y = 0;
    }
    return { 'x': x, 'y': y };
  },

  getHeatmapPoints(data, party, total) {
    // data is a list that looks like
    // [{  form: "You have the responsibility to do this",
    //     type: "ABSOLUTE_LIABILITY"},
    //  {...}, {...}, ...]
    var SCALE_MAX = 200;
    var SCALE = SCALE_MAX / (total * 0.45); //the scale as a fraction of the total liabilities.
    var INTENSITY = 0.5;
    var hmapPoints = [];

    // For Liabilities
    var sizeFunction = function(len) {
      //return len * SCALE;
      return Math.min(SCALE_MAX, (SCALE * len));
    };
    var intensityFunction = function(len, totlen, mod) {
      //return Math.min(len/5, 1);
      return mod * INTENSITY * (len / totlen);
    };

    // this will reshape data into an object that looks like
    // { "ABSOLUTE_LIABILITY": [{form: "...", type:"ABSOLUTE..."}, {f:'', t:'ABS'}, ...],
    //   "NO_LIABILITY": [{form: "...", type: "NO_LIABILITY"}, {f:'', t:'NO_L'}, ...] }
    var groupedData = {};
    _.each(data, function(sentence) {
      _.each(sentence.annotations, function(annotation) {
        //ensure that only the party being examined is included
        if (annotation.label === 'LIABILITY' && annotation.party === party) {
          if (groupedData[annotation.sublabel] === undefined) {
            groupedData[annotation.sublabel] = [];
          }
          groupedData[annotation.sublabel].push(sentence);
        }
      });
    });

    for (var type in groupedData) { // jshint ignore:line:wrap body of for
      if (groupedData.hasOwnProperty(type)) {
        var items = groupedData[type];
        var point = {};
        var mappedPoint = HeatmapLib.liabilityPoint(type, party);
        point.x = mappedPoint.x;
        point.y = mappedPoint.y;
        point.size = sizeFunction(items.length);
        //Greasy Blackfoot Hack to Lessen Them Intensity
        if (party === 'them') {
          point.intensity = intensityFunction(items.length, data.length, 1.6);
        } else {
          point.intensity = intensityFunction(items.length, data.length, 1.6);
        }
        //temporarily supress both liabilities from heatmap
        if (party !== 'both') {
          hmapPoints.push(point);
        }
      }
    }

    return hmapPoints;
  }
};


var Heatmap = React.createClass({

  getInitialState() {
    return {
      points: {
        you: 0, them: 0, both: 0
      }
    };
  },

  componentWillMount() {
    // instantiate heatmap element
    var canvas = ReactDOM.findDOMNode(this.refs.canvas);
    var heatmap = window.createWebGLHeatmap({
      canvas: canvas,
      intensityToAlpha: true,
      alphaRange: [0, 0.05]
    });
    this.setState({ heatmap: heatmap });
    this.forceUpdate(); // force componentDidUpdate()
  },

  componentDidUpdate() {
    var heatmap = this.getHeatMap();
    var points = this.getHeatmapPoints();
    heatmap.clear();
    heatmap.addPoints(points.you);
    heatmap.addPoints(points.them);
    heatmap.addPoints(points.both);
    heatmap.update();
    heatmap.display();
  },

  getHeatMap() {
    if (!this.heatmap) {
      this.heatmap = window.createWebGLHeatmap({
        canvas: this.refs.canvas,
        intensityToAlpha: true,
        alphaRange: [0, 0.05]
      });
    }
    return this.heatmap;
  },

  getHeatmapPoints() {
    const _getHeatmapPoints = HeatmapLib.getHeatmapPoints; // just an alias
    const liabs = this.getLiabilities();
    const all = liabs.you.length + liabs.them.length + liabs.both.length;
    return {
      you: _getHeatmapPoints(liabs.you, 'you', all),
      them: _getHeatmapPoints(liabs.them, 'them', all),
      both: _getHeatmapPoints(liabs.both, 'both', all)
    };
  },

  updateTooltip(evt) {
    var grid = ReactDOM.findDOMNode(this);
    var offset = $(grid).offset();

    const { parties } = this.props.analysis;

    const you = parties.you.name || 'You';
    const them = parties.them.name || 'Them';

    var x = evt.pageX - offset.left;
    var y = evt.pageY - offset.top;
    if (x<211 && y>78) {
      $(grid).attr('title', `${them}: Waive Liability`);
    } else if (x>211 && y>78) {
      $(grid).attr('title', `${you}: Waive Liability`);
    } else if (x>211 && y<78) {
      $(grid).attr('title', `${you}: Assumed Liability`);
    } else if (x<211 && y<78) {
      $(grid).attr('title', `${them}: Assumed Liability`);
    }
  },

  getLiabilities(props) {
    props = props || this.props;
    var allSentences = props.analysis.sentences;
    var allLiabilities = _.chain(allSentences)
      .filter(s => {
        var as = s.annotations;
        return as !== undefined && undefined !== _.find(as, { label: 'LIABILITY' });
      })
      .map(s => _.pick(s, 'annotations'))
      .value();

    function filterByParty(party) {
      return _.filter(allLiabilities, l => {
        return undefined !== _.find(l.annotations,
                                    { 'party': party, label: 'LIABILITY' });
      });
    }

    return {
      you: filterByParty('you'),
      them: filterByParty('them'),
      both: filterByParty('both')
    };
  },

  render() {
    var width = 420,
      height = 160;

    var liabilities = this.getLiabilities();

    var themName = this.props.analysis.parties.them.name;
    var youName = this.props.analysis.parties.you.name;

    var you = liabilities.you.length, // party A
      them = liabilities.them.length, // party B
      both = liabilities.both.length; // both

    function toPercent(num) {
      return num.toFixed(6) * 100 + '%';
    }

    var scale = Math.max(0.0001, them+both+you);
    var widthA = you/scale,
      widthB = them/scale,
      widthBoth = both/scale;

    var partyBLine = {
      width: toPercent(widthB)
    };
    var partyBothLine = {
      width: toPercent(widthBoth),
      left: toPercent(widthB)
    };
    var partyALine = {
      width: toPercent(widthA),
      left: toPercent(widthB+widthBoth)
    };

    return (
      <div>
        <div className="liab-bg">
          <div className="liab-line partyb" style={partyBLine} />
          <div className="liab-line both" style={partyBothLine} />
          <div className="liab-line partya" style={partyALine} />
        </div>
        <div className="heatmap" onMouseMove={this.updateTooltip}>
          <img src="/static/img/heatmapgrid.png" id="liabilitiesGrid"
            width={width} height={height} />
          <span className="them-label">{themName}</span>
          <span className="you-label">{youName}</span>
          <canvas ref="canvas" width={width} height={height} />
        </div>
      </div>
    );
  }

});


var LiabilitiesWidget = React.createClass({

  render() {
    const isLoaded = this.props.analysis && this.props.analysis.sentences.length !== 0;
    const parties = this.props.analysis && this.props.analysis.parties;

    var body = (isLoaded) ?
      <Heatmap analysis={this.props.analysis} /> :
      <Spinner />;

    return (
      <Widget title="Liabilities" className="Liabilities" icon={isLoaded} parties={parties}>
        {body}
      </Widget>
    );
  }
});


module.exports = LiabilitiesWidget;
