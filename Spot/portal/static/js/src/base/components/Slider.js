import React, { PropTypes } from 'react';
import Slider from 'rc-slider';
import { connect } from 'react-redux';
import NumericInput from 'react-numeric-input';
import InfoIcon from 'base/components/InfoIcon';

import 'rc-slider/assets/index.css';

class CustomSlider extends React.Component {
  constructor(props) {
    super(props)
  }

  render(){
    const {
      handleSliderChange,
      sliderPercentage,
      labelLeft,
      labelRight,
      infoMessage,
      small,
      sliderOptions,
      inputOptions
    } = this.props;

    const formatPc = p => p + ' %';

    const style = small ? { width: '65px' } : { width: '300px' };
    const railStyle = small ? { backgroundColor: '#838383', height: 1 } : { backgroundColor: '#ddccef', height: 10, marginTop: -4 };
    const trackStyle = small ? { backgroundColor: '#0183FD', height: 1 } : { backgroundColor: '#b99cd6', height: 10, marginTop: -4 };
    const handleStyle = small ? (
      {
        border: 0,
        height: 9,
        width: 9,
        marginLeft: -4,
        marginTop: -4,
        backgroundColor: '#4784B1'
      }
    ) : (
      {
        borderColor: '#69c6d1',
        height: 20,
        width: 20,
        marginLeft: -14,
        marginTop: -9,
        backgroundColor: '#69c6d1',
      }
    )

    return(
      <div className="slider">
        <div className="slider-wrapper" style={style}>
          <Slider
            value={sliderPercentage}
            onChange={handleSliderChange}
            tipTransitionName="rc-slider-tooltip-zoom-down"
            defaultValue={sliderPercentage}
            railStyle={railStyle}
            trackStyle={trackStyle}
            tipFormatter={formatPc}
            handleStyle={handleStyle}
            {...sliderOptions}
          />
        </div>
        <div className={`slider-input ${small ? 'slider-input--small' : ''}`}>
          <NumericInput
            min={0}
            max={100}
            value={sliderPercentage}
            format={formatPc}
            onChange={handleSliderChange}
            {...inputOptions} />
        </div>
        { infoMessage && <InfoIcon messagesMap={infoMessage} /> }
        { labelLeft && labelRight && (
          <div className="slider-labels">
            <div className="slider-label">{ labelLeft }</div>
            <div className="slider-label">{ labelRight }</div>
          </div>
        ) }
      </div>
    )
  }
}

export default connect()(CustomSlider);
