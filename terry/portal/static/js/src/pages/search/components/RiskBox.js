import React from 'react';

//used to lighten or brighten a color
import Color from 'color';
import '../scss/RiskBox.scss';

//constants
const lowLeftLid = -10;
const lowRightLid = 190;
const openColor = {
  r:102,
  g:230,
  b:180
}
const closedColor = {
  r:180,
  g:0,
  b:255
}

class RiskBox extends React.Component {
  constructor(props) {
    super(props);
    this.state = { boxHover: false };
  }

  calcLeftLidAngle(score) {
    return lowLeftLid + (score * 190) / 100;
  }

  calcRightLidAngle(score) {
    return lowRightLid - (score * 190) / 100;
  }

  clacBoxColor(score,lighten) {

    const shade = lighten ? lighten : 0;

    const redInterval = closedColor.r - openColor.r;
    const greenInterval = closedColor.g - openColor.g;
    const blueInterval = closedColor.b - openColor.b;

    const boxColor = {
      r:Math.floor(openColor.r + ((redInterval * score)/100)),
      g:Math.floor(openColor.g + ((greenInterval * score)/100)),
      b:Math.floor(openColor.b + ((blueInterval * score)/100))
    }

    return `rgb(${boxColor.r},${boxColor.g},${boxColor.b})`;
  }

  render() {
    const { score } = this.props;

    const leftLidAngle = this.calcLeftLidAngle(score);
    const rightLidAngle = this.calcRightLidAngle(score) ;

    const normalBoxColor = this.clacBoxColor(score);
    const lighenBoxColor = Color(normalBoxColor).lighten(0.05).rgb().string();
    const darkenBoxColor = Color(normalBoxColor).darken(0.05).rgb().string();
    const valueColor = Color(normalBoxColor).darken(0.35).rgb().string();

    const leftLidStyle = {
      transform: `rotateY(${leftLidAngle}deg) translateX(-1.5em)`,
      backgroundColor: darkenBoxColor
    }
    const rightLidStyle = {
      transform: `rotateY(${rightLidAngle}deg) translateX(1.5em)`,
      backgroundColor: normalBoxColor
    }

    const darkColorStyle = { backgroundColor: darkenBoxColor };
    const brightColorStyle = { backgroundColor: lighenBoxColor };
    const normalColorStyle = { backgroundColor: normalBoxColor };
    const valueTextColorStyle = { color: valueColor };

    return (
      <span
        onMouseOver={()=>{this.setState({boxHover:true})}}
        onMouseLeave={()=>{this.setState({boxHover:false})}}>
        <div className="risk-box-wrap">
          <div className="perspective">
            <div className="cube">
              <div className="cube-left" style={darkColorStyle}>
                <div className="score">
                  {100 - score}%
                </div>
              </div>
              <div className="cube-right" style={normalColorStyle}></div>

              <div className="cube-back-left" style={brightColorStyle}></div>
              <div className="cube-back-right" style={brightColorStyle}></div>

              <div className="cube-right-lid" style={rightLidStyle}></div>
              <div className="cube-left-lid" style={leftLidStyle}></div>
            </div>
          </div>
        </div>
        <div className='risk-info'>
          <span className="risk-info-title">Terry score</span>
          Your dependency stack is
          <span className="risk-info-value" style={valueTextColorStyle}>{100 - score}% open</span>
        </div>
      </span>
    )
  }
}

export default RiskBox;
