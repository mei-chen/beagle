import React, { Component, PropTypes } from 'react';
import * as d3 from 'd3';
import Slider from 'rc-slider';
import { Modal, ModalHeader, ModalBody, Pagination } from 'react-bootstrap';

class ThresholdChart extends Component {
  constructor(props) {
    super(props);
    this._handleSliderChange = this._handleSliderChange.bind(this);
    this._renderBars = this._renderBars.bind(this);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._renderSamples = this._renderSamples.bind(this);
    this._handlePaginationClick = this._handlePaginationClick.bind(this);
    this.SHOW_SAMPLES = 10;

    const { data, range, width, height, colors } = props;

    // init data variables
    const bucketLength = data[0].length; // intervals from 0 to 1 (pos and neg has the same length)
    const seriesLength = 2; // bars inside one interval

    const yMax = d3.max([].concat.apply([], data));

    // init d3 functions
    this.y = d3.scale.linear()
      .domain([0, yMax])
      .range([0, height]);

    this.x0 = d3.scale.ordinal() // bands
      .domain(d3.range(0, bucketLength))
      .rangeBands([0, width], .3, .25);

    this.x1 = d3.scale.ordinal() // bars inside bands
      .domain(d3.range(seriesLength))
      .rangeBands([0, this.x0.rangeBand()]);

    this.xThreshold = d3.scale.linear() // threshold
      .domain(range)
      .range([0, width])

    this.state = {
      showModal: false,
      modalSamples: [],
      modalSamplesStatus: null,
      pageNum: 1
    }
  }

  _renderBars(data) {
    const { height, colors } = this.props;

    return data.map((row, rowI) => (
      <g
        key={rowI}
        fill={colors[rowI]}
        transform={`translate(${this.x1(rowI)}, 0)`}>
        {
          row.map((item, itemI) => (
            <g
              key={itemI}
              className="threshold-chart-column"
              onClick={() => this._showModal(item, itemI, rowI)}>
              { item !== 0 && ( // rectangle for column hover effect
                <rect
                  className={`threshold-chart-hover-bar ${rowI === 0 ? 'threshold-chart-hover-bar--true' : 'threshold-chart-hover-bar--false'}`}
                  width={this.x1.rangeBand()}
                  height={height}
                  x={this.x0(itemI)}
                  y={0} />
              ) }
              <rect
                className="threshold-chart-bar"
                width={this.x1.rangeBand()}
                height={this.y(item)}
                x={this.x0(itemI)}
                y={height - this.y(item)} />
            </g>
          ))
        }
      </g>
    ))
  }

  _handleSliderChange(value) {
    const { onChange } = this.props;
    onChange(value);
  }

  _showModal(item, itemI, rowI) {
    const { samples } = this.props;
    const positive = rowI === 0;
    this.setState({
      showModal: true,
      pageNum: 1,
      modalSamples: samples[rowI][itemI],
      modalSamplesStatus: positive ? 'pos' : 'neg'
    })
  }

  _hideModal() {
    this.setState({ showModal: false })
  }

  _renderSamples(samples, status) {
    return samples.map((sample, i) => (
      <div
        key={i}
        className={`dataset-preview-item dataset-preview-item--${status}`}>
        { sample }
      </div>
    ));
  }

  _handlePaginationClick(pageNum) {
    this.setState({ pageNum });
  }

  render() {
    const { data, range, threshold, width, height, colors, hoverColors, lineColor } = this.props;
    const { showModal, modalSamples, modalSamplesStatus, pageNum } = this.state;

    return (
      <div className="threshold">
        <svg
          className="threshold-chart"
          width={width+1} /* 1px for max threshold line position */
          height={height}>

          {/* hover gradients */}
          <defs>
            <linearGradient id="threshold-hover-gradient-true" x2="0" y2="100%">
              <stop offset="0%" style={{ stopColor: '#fff' }} />
              <stop offset="100%" style={{ stopColor: hoverColors[0] }} />
            </linearGradient>
            <linearGradient id="threshold-hover-gradient-false" x2="0" y2="100%">
              <stop offset="0%" style={{ stopColor: '#fff' }} />
              <stop offset="100%" style={{ stopColor: hoverColors[1] }} />
            </linearGradient>
          </defs>

          {/* bars */}
          <g className="threshold-chart-bars">
            { this._renderBars(data) }
          </g>

          {/* line */}
          <g
            className="threshold-chart-line"
            fill="red">
            <rect
              width={1}
              height={height}
              y={0}
              x={this.xThreshold(threshold)}
              fill={lineColor} />
          </g>
        </svg>

        {/* slider */}
        <div style={{ width }}>
          <Slider
            className="threshold-slider"
            width={width}
            value={threshold}
            min={range[0]}
            max={range[1]}
            step={0.01}
            onChange={this._handleSliderChange}
            defaultValue={threshold}
            trackStyle={{ backgroundColor: colors[1] }}
            railStyle={{ backgroundColor: colors[0] }}
            handleStyle={{ backgroundColor: lineColor }} />
        </div>

        <div
          className="threshold-value">
          <span
            className="threshold-value-inner"
            style={{
              color: threshold !== 0 ? lineColor : '#000',
              left: `${this.xThreshold(threshold)}px`
            }}>
            { threshold }
          </span>
        </div>

        <Modal
          show={showModal}
          onHide={this._hideModal}
          className="threshold-modal">
          <ModalHeader closeButton>
            <h4>Samles</h4>
          </ModalHeader>
          <ModalBody>
            { modalSamples.length > 0 && (
              <div className="threshold-samples">
                { this._renderSamples(modalSamples.slice((pageNum - 1) * this.SHOW_SAMPLES, (pageNum - 1) * this.SHOW_SAMPLES + this.SHOW_SAMPLES), modalSamplesStatus) }
              </div>
            ) }

            <div className="text-center">
              { modalSamples.length > this.SHOW_SAMPLES && (
                <Pagination
                  prev
                  next
                  ellipsis
                  boundaryLinks
                  items={Math.ceil(modalSamples.length / this.SHOW_SAMPLES)}
                  maxButtons={5}
                  activePage={pageNum}
                  onSelect={this._handlePaginationClick} />
              ) }
            </div>
          </ModalBody>
        </Modal>
      </div>
    );
  }
}

ThresholdChart.propTypes = {
  data: PropTypes.array.isRequired, // [ [pos], [neg] ]
  samples: PropTypes.array.isRequired, // [ [pos1, pos2 ...], [neg1, neg2 ...] ]
  range: PropTypes.array.isRequired,
  threshold: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  width: PropTypes.number,
  height: PropTypes.number,
  colors: PropTypes.array,
  hoverColors: PropTypes.array,
  lineColor: PropTypes.string
};

ThresholdChart.defaultProps = {
  width: 200,
  height: 90,
  colors: ['#377D22', '#CDB591'],
  hoverColors: ['#C9D8C2', '#e1d2bc'],
  lineColor: '#5583AD'
};

export default ThresholdChart;
