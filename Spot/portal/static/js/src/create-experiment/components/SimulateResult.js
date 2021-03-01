import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';
import escape from 'escape-html';

class SimulateResult extends Component {
  constructor(props) {
    super(props);
    this._getClfIconClass = this._getClfIconClass.bind(this);
    this._highlightSample = this._highlightSample.bind(this);
    this._getStatusBorderColor = this._getStatusBorderColor.bind(this);
    this._getStatusColor = this._getStatusColor.bind(this);
    this._wrapWord = this._wrapWord.bind(this);
  }

  _getClfIconClass(type) {
    switch(type) {
      case 'regex':   return 'fa fa-superscript';
      case 'builtin': return 'fa fa-archive';
      case 'trained': return 'fa fa-magic';
    }
  }

  _highlightSample(sample) {
    return sample.map(pair => {
      const word = pair.get(0),
            confidence = pair.get(1);
      return confidence > 0 ? this._wrapWord(escape(word), confidence) : escape(word);
    }).join(' ');
  }

  _wrapWord(word, confidence) {
    return `<span title="${confidence.toFixed(1)}" style="background-color: rgba(32, 155, 109, ${(confidence).toFixed(1)})">${word}</span>`
  }

  _getStatusColor(status, weight) {
    return status === true ? `rgba(32, 155, 109, ${weight})` : `rgba(191, 104, 104, ${weight})`
  }

  _getStatusBorderColor(status) {
    return status === true ? 'rgb(32, 155, 109)' : 'rgb(191, 104, 104)'
  }

  render() {
    const { name, type, weight, sample, status, short } = this.props;

    return (
      <div
        className="smlt">
        { !short && (
          <div className="smlt-details">
            <span 
              className="smlt-status" 
              style={{ backgroundColor: this._getStatusColor(status, weight), borderColor: this._getStatusBorderColor(status) }}/>
            <span className="smlt-info">
              <i className="fa fa-balance-scale" /> { `${weight * 100}%` }
            </span>
            <span className="smlt-info">
              <i className={`${this._getClfIconClass(type)}`} /> { name }
            </span>
          </div>
        ) }

        { !!sample && sample.size > 0 && <div className="smlt-sample" dangerouslySetInnerHTML={{ __html: this._highlightSample(sample) }} /> }
      </div>
    )
  }
};

SimulateResult.propTypes = {
  short: PropTypes.bool,
  sample: PropTypes.instanceOf(List),
  name: PropTypes.string,
  type: PropTypes.string,
  weight: PropTypes.number,
  status: PropTypes.bool
};

export default SimulateResult;
