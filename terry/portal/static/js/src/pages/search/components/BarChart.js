import React, { Component, PropTypes } from 'react';
import * as d3 from 'd3';

class BarChart extends Component {
  constructor(props) {
    super(props);
    this._getSum = this._getSum.bind(this);
    this._sortData = this._sortData.bind(this);
    this._renderBar = this._renderBar.bind(this);
    this._renderBoxes = this._renderBoxes.bind(this);
    this._getGradient = this._getGradient.bind(this);
    this._toggleDrop = this._toggleDrop.bind(this);
    this._isInt = this._isInt.bind(this);
    this._mean = this._mean.bind(this);

    const { lowColor, highColor } = props;

    // init color function
    this.color = d3.scale.linear()
                         .domain([0, 1])
                         .range([d3.rgb(lowColor), d3.rgb(highColor)]);

    this.state = {
      isOpen: !!this.props.open
    }
  }

  _getSum(data) {
    return data.reduce((total, item) => total += item.value, 0)
  }

  _sortData(data) {
    return data.sort((a, b) => {
      if(a.value < b.value) return 1;
      if(a.value > b.value) return -1;
      return 0;
    });
  }

  _getGradient(color) {
    const rgb = d3.rgb(color);
    const OFFSETS = [25, 41.7, 58.3, 75];
    const OPACITIES = [0.5, 0.375, 0.25, 0.125];
    const result = [];

    for(let i = 0; i < OFFSETS.length; i++) {
      result.push(`rgba(${rgb.r},${rgb.g},${rgb.b},${OPACITIES[i]}) ${OFFSETS[i]}%`)
    }

    return result.join(',');
  }

  _renderBar(value) {
    if(value === null) return null;

    const { barHeight } = this.props;
    const color = this.color(value);
    const gradient = this._getGradient(color);

    return (
      <div
        className="chart-bar"
        style={{
          height: `${value * barHeight}px`,
          borderTopColor: color,
          background: `linear-gradient(${gradient})`
        }}>
      </div>
    )
  }

  _isInt(num) {
    return num % 1 === 0;
  }

  _mean(arr) {
    return arr.reduce((sum, value) => sum += value, 0) / arr.length;
  }

  _renderBoxes(data) {
    const { width:areaWidth, colors } = this.props;
    const TRIANGLE_MAX_WIDTH = 10;
    const sorted = this._sortData(data);
    const sum = this._getSum(data);
    let colorIndex = 0;

    return sorted.map((item, i) => {
      const portion = item.value / sum;
      const boxWidth = portion * areaWidth;
      const percent = +(portion * 100).toFixed(1);
      const triangleWidth = Math.min(boxWidth - 2, TRIANGLE_MAX_WIDTH); // 2 = box white border width
      const isBarsData = item.barsData.indexOf(null) === -1;
      const bubbleColor = this.color(this._mean(item.barsData));

      if(i % colors.length === 0) colorIndex = 0; // if not not enough colors

      const box = (
        <div
          key={i}
          className="chart-box"
          style={{ width: `${boxWidth}px` }}>

          <div className="chart-column">
            {/* bars */}
            { !isBarsData ? (
              <div className="chart-bar chart-bar--no-data" />
              ) : (
              <div className="chart-bars">
                { item.barsData.map((value, i) => (
                  <div key={i}>{ this._renderBar(value) }</div>
                )) }
                <span
                  className="chart-bars-bubble"
                  style={{ backgroundColor: bubbleColor }}>
                  { `${this._mean(item.barsData) * 100}%` }
                  <span
                    className="chart-bars-bubble-triangle"
                    style={{ borderTopColor: bubbleColor }} />
                </span>
              </div>
            ) }

            {/* chart bottom piece */}
            <div
              className="chart-piece"
              style={{ backgroundColor: colors[colorIndex] }}
              onClick={this._toggleDrop}>
              <span
                className="chart-piece-triangle"
                style={{ borderLeftWidth: `${triangleWidth}px`, borderTopColor: colors[colorIndex] }}>
              </span>
              <span
                className="chart-piece-label">
                  <strong>{ `${item.label}` }</strong>
                  <span className="chart-piece-percent">
                    <i className="fa fa-chart-pie" />
                    { `${this._isInt(percent) ? percent.toFixed(0) : percent}%` }
                  </span>
              </span>
            </div>
          </div>
        </div>
      );

      colorIndex++;

      return box;
    })
  }

  _toggleDrop() {
    this.setState({ isOpen: !this.state.isOpen });
  }

  render() {
    const { title, subtitle, data, width } = this.props;
    const { isOpen } = this.state;
    return (
      <div
        className="chart-row"
        style={{ width: `${width}px` }}>

        <strong
          className="chart-categ">
          { title }
          { subtitle ? <span className="chart-categ-subtitle">{ `(${subtitle})` }</span> : null }
        </strong>


        <span
          className={`chart-toggle ${isOpen ? 'chart-toggle--open' : ''}`}
          onClick={this._toggleDrop}>
          <i className="fa fa-chart-bar" />
          <span>{isOpen ? 'Risk chart' : 'Show risk chart'}</span>
          <i className={`chart-toggle-chevron fa ${isOpen ? 'fa-chevron-up' : 'fa-chevron-down'}`} />
        </span>

        <div className={`chart-area ${isOpen ? 'chart-area--open' : ''}`}>{ this._renderBoxes(data) }</div>
      </div>
    )
  }
}

BarChart.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  data: PropTypes.array.isRequired,
  width: PropTypes.number.isRequired,
  colors: PropTypes.array.isRequired,
  barHeight: PropTypes.number.isRequired,
  lowColor: PropTypes.string.isRequired,
  highColor: PropTypes.string.isRequired,
  open: PropTypes.bool
};

BarChart.defaultProps = {
  width: 780,
  colors: ['#03a9f4', '#009688', '#4caf50', '#8bc34a'],
  barHeight: 60,
  lowColor: '#66e6b4',
  highColor: '#b400ff'
};

export default BarChart;
