import React, { Component, PropTypes } from 'react';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import { FormControl } from 'react-bootstrap';

class Weight extends Component {
  constructor(props) {
    super(props);
    this._handleInputChange = this._handleInputChange.bind(this);
    this._prepareToSave = this._prepareToSave.bind(this);
    this._prepareToDisplay = this._prepareToDisplay.bind(this);
    this.state = {
      weight: this._prepareToDisplay(this.props.weight)
    }
  }

  _prepareToSave(value) {
    if( isNaN(+value) || value === '') return 0;
    if(+value > 100) return 100;
    if(+value % 1 !== 0) return Number((+value).toFixed(2))
    return +value;
  }

  _prepareToDisplay(value) {
    // fix floating point
    // integer
    if( (value*100).toFixed(2) % 1 === 0 ) return (value*100).toFixed(0);
    // decimal
    return (value*100).toFixed(2);
  }

  _handleInputChange(e) {
    const value = e.target.value;
    this.setState({ weight: value });
    this.props.onChange( this._prepareToSave(value) / 100 );
  }

  render() {
    const { isEdit, weight, onChange } = this.props;
    const tooltip = <Tooltip id="voting_weight">Voting weight</Tooltip>;

    const weight_style = {
      backgroundColor:'rgba(222, 212, 122, '+ weight +')',
    }

    return (
      <OverlayTrigger placement="top" overlay={tooltip}>
        <span className="clf-weight" style={weight_style}>
        <i className="fa fa-percent"/>
        { isEdit ? (
          <FormControl
          type="text"
          className="clf-weight-input"
          value={this.state.weight}
          onChange={this._handleInputChange} />
        ) : (
          <span>{ this._prepareToDisplay(weight) }</span>
        ) }
        </span>
      </OverlayTrigger>
    )
  }
}

Weight.propTypes = {
  weight: PropTypes.number.isRequired,
  isEdit: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired
}

export default Weight;
