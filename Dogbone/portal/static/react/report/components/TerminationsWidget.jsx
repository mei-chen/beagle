import _ from 'lodash';
import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import { select, selection, event } from 'd3';
import venn from 'utils/venn';
import { NoData } from './NoData';
import Widget from './Widget';
import Spinner from './Spinner';

const d3Chart = {};


d3Chart.getSets = function(state) {
  /* see http://nicolashery.com/integrating-d3js-visualizations-in-a-react-app/
   * for more information */
  if (state.analysis == null) {
    return;
  }

  let { parties, sentences } = state.analysis;

  let countedTerminations = {
    you: 0, them: 0, both: 0, none: 0
  };
  sentences.forEach(s => {
    let annotations = s.annotations || [];
    annotations.forEach(a => {
      if (a.label === 'TERMINATION') {
        countedTerminations[a.party]++;
      }
    });
  });

  const terminationsYOU = countedTerminations.you;
  const terminationsTHEM = countedTerminations.them;
  const terminationsBOTH = countedTerminations.both;
  const you = parties.you.name;
  const them = parties.them.name;

  //Them: #28A3D4
  //You: #E3E346
  //------------
  //Maroon: #A5424B
  //Grey #AFAFAF
  // get positions for each set
  const sets = [{
    label: them, size: terminationsTHEM + terminationsBOTH
  }, {
    label: you, size: terminationsYOU + terminationsBOTH
  }];
  const overlaps = [{
    sets: [0, 1], size: terminationsBOTH
  }];

  // (George) I'm not sure what each of these really are.
  // I'm just returning all of them and using them as originally used
  return {
    sets: venn.venn(sets, overlaps),
    rawSets: sets,
    overlaps: overlaps
  };
};

d3Chart.update = function(diagram, state) {
  const { sets } = d3Chart.getSets(state);
  venn.updateD3Diagram(diagram, sets);

  //Get elements to hold the original svg points
  const circlea = select(diagram.circles._groups[0][0]);
  const circleb = select(diagram.circles._groups[0][1]);
  const texta = select(diagram.text._groups[0][0]);
  const textb = select(diagram.text._groups[0][1]);
  //Get the center of the circles
  const orig1 = this.orig1;
  const orig2 = this.orig2;
  //Get the party names text original position
  const torig1 = this.torig1;
  const torig2 = this.torig2;

  // Move the circles apart initially
  circlea.transition()
    .attr('cx', () => +orig1 - 50);
  circleb.transition()
    .attr('cx', () => +orig2 + 50);
  texta.transition()
    .attr('x', () => +torig1 - 30);
  textb.transition()
    .attr('x', () => +torig2 + 30);
};

d3Chart.create = function(el, style, state) {
  // draw the diagram in the 'venn' div
  const { sets, overlaps } = d3Chart.getSets(state);
  const diagram = venn.drawD3Diagram(select(el), sets, 430, 180);

  // add a tooltip showing the size of each set/intersection
  const tooltip = select('body')
    .append('div')
    .attr('class', 'venntooltip')
    .style('opacity', 0);

  //style the circles
  const circleColours = ['#28A3D4', '#E3E346'];
  const textColours = ['#000', '#000'];

  diagram.circles
    .style('fill-opacity', 0.7)
    .style('stroke-width', '2')
    .style('stroke-opacity', 0.8)
    .style('fill', function(d, i) { return circleColours[i]; })
    .style('stroke', '#FAFAFA')
    .style('stroke-width', '2');

  diagram.text
    .style('fill', function(d, i) { return textColours[i]; })
    .style('fill-opacity', 1.0);

  selection.prototype.moveParentToFront = function() {
    return this.each(function() {
      this.parentNode.parentNode.appendChild(this.parentNode);
    });
  };

  //Get elements to hold the original svg points
  const circlea = select(diagram.circles._groups[0][0]);
  const circleb = select(diagram.circles._groups[0][1]);
  const texta = select(diagram.text._groups[0][0]);
  const textb = select(diagram.text._groups[0][1]);
  //Get the center of the circles
  const orig1 = circlea.attr('cx');
  const orig2 = circleb.attr('cx');
  //Get the party names text original position
  const torig1 = texta.attr('x');
  const torig2 = textb.attr('x');

  // save original start positions to the d3chart object
  d3Chart.orig1 = orig1;
  d3Chart.orig2 = orig2;
  d3Chart.torig1 = torig1;
  d3Chart.torig2 = torig2;

  // attach callbacks for animating the circles
  diagram.svg
    .on('mouseover', function() {
      //Move circles & text inward
      circlea.transition()
        .attr('cx', function() { return orig1; });
      circleb.transition()
        .attr('cx', function() { return orig2; });
      texta.transition()
        .attr('x', function() { return torig1; });
      textb.transition()
        .attr('x', function() { return torig2; });
    })
    .on('mouseout', function() {
      //Move circles & text outward
      circlea.transition()
        .attr('cx', function() { return +orig1 - 50; });
      circleb.transition()
        .attr('cx', function() { return +orig2 + 50; });
      texta.transition()
        .attr('x', function() { return +torig1 - 30 ; });
      textb.transition()
        .attr('x', function() { return +torig2 + 30 ; });
    });

  diagram.nodes
    .on('mousemove', function() {
      tooltip.style('left', (event.pageX) + 'px')
        .style('top', (event.pageY - 28) + 'px');
    })
    .on('mouseover', function(d) {
      const selection = select(this).select('circle');
      selection.moveParentToFront()
        .transition()
        .style('fill-opacity', 0.9)
        .style('stroke-opacity', 1);
      tooltip.transition().style('opacity', 0.9);
      if (d.size !== 1) {
        tooltip.text(d.size + ' options');
      } else {
        tooltip.text(d.size + ' option');
      }
    })
    .on('mouseout', function() {
      select(this).select('circle').transition()
        .style('fill-opacity', 0.7)
        .style('stroke-opacity', 0);
      tooltip.transition().style('opacity', 0);
    });

  // draw a path around each intersection area, add hover there as well
  diagram.svg.selectAll('path')
    .data(overlaps)
    .enter()
    .append('path')
    .attr('d', function(d) {
      return venn.intersectionAreaPath(d.sets.map(j => sets[j]));
    })
    .style('fill-opacity', 0)
    .style('fill', 'black')
    .style('stroke-opacity', 0)
    .style('stroke', 'white')
    .style('stroke-width', 2)
    .on('mouseover', function(d) {
      select(this).transition()
        .style('fill-opacity', 0.1)
        .style('stroke-opacity', 1);
      tooltip.transition().style('opacity', 0.9);
      if (d.size !== 1) {
        tooltip.text(d.size + ' options');
      } else {
        tooltip.text(d.size + ' option');
      }
    })
    .on('mouseout', function() {
      select(this).transition()
        .style('fill-opacity', 0)
        .style('stroke-opacity', 0);
      tooltip.transition().style('opacity', 0);
    })
    .on('mousemove', function() {
      tooltip
        .style('left', (event.pageX) + 'px')
        .style('top', (event.pageY - 28) + 'px');
    });

  // return the diagram object for update
  return diagram;
};

/* jshint unused:false */
d3Chart.destroy = function() {};

/* jshint unused:true */


const TerminationsChart = React.createClass({

  componentDidMount() {
    const el = ReactDOM.findDOMNode(this);
    const style = {
      width: '100%',
      height: '300px'
    };
    const diagram = d3Chart.create(el, style, this.getChartState());
    this._diagram = diagram;
    // call a force update to make the venn circles move apart
    this.forceUpdate();
  },

  componentDidUpdate() {
    const diagram = this._diagram;
    d3Chart.update(diagram, this.getChartState());
  },

  componentWillUnmount() {
    const el = ReactDOM.findDOMNode(this);
    d3Chart.destroy(el);
  },

  getChartState() {
    return {
      analysis: this.props.analysis,
    };
  },

  render() {
    return <div/>;
  }

});


const TerminationsWidget = React.createClass({

  componentWillUnmount() {
    $('.venntooltip').remove();
  },

  hasTerminations() {
    const analysis = this.props.analysis;
    if (analysis === undefined) {
      return false;
    }
    const sentences = analysis.sentences;
    const terminations = _.filter(sentences, sentence => {
      return _.find(sentence.annotations, { label: 'TERMINATION' }) !== undefined;
    });
    return terminations.length > 0;
  },

  render() {
    const isLoaded = this.props.analysis && this.props.analysis.sentences.length !== 0;
    const hasTerminations = this.hasTerminations();
    let content;

    if (isLoaded) {
      if (hasTerminations) {
        content = <TerminationsChart analysis={this.props.analysis} />;
      } else {
        content = <NoData />;
      }
    } else {
      content = <Spinner />;
    }

    return (
      <Widget title="Terminations" className="Terminations">
        {content}
      </Widget>
    );
  }
});


module.exports = TerminationsWidget;
