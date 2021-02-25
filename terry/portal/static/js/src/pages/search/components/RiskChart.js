import React, { Component, PropTypes } from 'react';
import * as d3 from "d3";


class RiskChart extends Component {
  constructor(props) {
    super(props);
    this.x = this.x.bind(this);
    this.y = this.y.bind(this);
    this.meanY = this.meanY.bind(this);
    this.gradientY = this.gradientY.bind(this);
    this.percentageX = this.percentageX.bind(this);
    this.area = this.area.bind(this);
    this.line = this.line.bind(this);
  }

  y(...args) {
    const { yMargin, height } = this.props;

    return d3.scale.linear()
                   .domain([0, 1])
                   .range([yMargin, height - yMargin])
                   .apply(null, args)
  }

  x(...args) {
    const { xMargin, width, data } = this.props;

    return d3.scale.linear()
                   .domain([0, data.length - 1])
                   .range([xMargin, width - xMargin])
                   .apply(null, args);
  }

  meanY() {
    const { data } = this.props;

    return d3.mean(data)
  }

  gradientY(...args) {
    const { lowColor, highColor } = this.props;

    return d3.scale.linear()
                   .domain([0, 1])
                   .range([d3.rgb(lowColor), d3.rgb(highColor)])
                   .apply(null, args);
  }

  percentageX(...args) {
    const { data } = this.props;
    const percentageMargin = 100 / data.length;

    return d3.scale.linear()
                   .domain([0, data.length - 1])
                   .range([percentageMargin, 100 - percentageMargin])
                   .apply(null, args);
  }

  area(...args) {
    const { height } = this.props;
    const self = this;

    return d3.svg.area()
                 .interpolate("cardinal")
                 .x(function(d,i) { return self.x(i); })
                 .y0(height)
                 .y1(function(d) { return height - self.y(d); })
                 .apply(null, args);
  }

  line(...args) {
    const { height } = this.props;
    const self = this;

    return d3.svg.line()
                 .interpolate("cardinal")
                 .x(function(d, i) { return self.x(i); })
                 .y(function(d) { return height - self.y(d); })
                 .apply(null, args);
  }

  render() {
    const { width, height, id, data } = this.props;

    return (
      <div className="risk-chart">
        <svg
          width={width}
          height={height}>
          <g
            stroke={`url(#sparkline-gradient-${id})`}
            fill={`url(#sparkline-gradient-${id})`}>
            <path d={this.line(data)} />
            <path
              d={this.area(data)}
              style={{ fill: `url(#area-fill-${id})`, stroke: 'none' }}
            />
          </g>
          <defs>

            <linearGradient
              id={`sparkline-gradient-${id}`}
              x1="0%" y1="0%" x2="100%" y2="0%"
              gradientUnits="userSpaceOnUse">
              { data.map((item, i) => (
                <stop
                  key={i}
                  offset={this.percentageX(i) + '%'}
                  style={{ stopColor: this.gradientY(item), stopOpacity: 1 }} />
              )) }
            </linearGradient>

            <linearGradient
              id={`area-fill-${id}`}
              x1="0%" y1="0%" x2="0%" y2="100%"
              gradientUnits="userSpaceOnUse">
              { data.map((item, i) => (
                <stop
                  key={i}
                  offset={this.percentageX(i) + '%'}
                  style={{ stopColor: this.gradientY(this.meanY()), stopOpacity: 0.5 - i / parseFloat(data.length*2) }} />
              )) }
            </linearGradient>
          </defs>
        </svg>
      </div>
    )
  }
}

RiskChart.propTypes = {
  id: PropTypes.string.isRequired,
  data: PropTypes.array.isRequired,
  width: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired,
  xMargin: PropTypes.number.isRequired,
  yMargin: PropTypes.number.isRequired,
  lowColor: PropTypes.string.isRequired,
  highColor: PropTypes.string.isRequired
};

RiskChart.defaultProps = {
  width: 100,
  height: 30,
  xMargin: 0,
  yMargin: 3,
  lowColor: '#66e6b4',
  highColor: '#b400ff'
}

export default RiskChart;
