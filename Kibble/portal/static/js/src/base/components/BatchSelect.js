import React from "react";
import PropTypes from 'prop-types';
import ImmutablePropTypes from 'react-immutable-proptypes';
import { List } from 'immutable';
import { FormGroup, ControlLabel } from 'react-bootstrap';
import { batchPropType } from 'BatchManagement/propTypes';
import Select from 'react-select';
import 'react-select/dist/react-select.css';


class BatchSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      option: null
    };

    this.getOptions = this.getOptions.bind(this);
    this.onChange = this.onChange.bind(this);
  }

  getOptions() {
    const batches = this.props.batches.toJS();
    return batches.map((batch) => ({ value: batch.id, label: batch.name }))
  };

  onChange(option) {
    this.setState({ option: option ? option.value : 0 });
    this.props.onChange(option ? option.value : 0)
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.doClear) {
      this.onChange(null);
      this.props.doClearDone();
    }
  }

  render() {
    if (!this.props.display) return null;
    if (this.props.batches.size) {
      return (
        <FormGroup>
          <ControlLabel>{ this.props.title }</ControlLabel>
          <Select
            name={this.props.name}
            value={this.state.option}
            options={this.getOptions()}
            onChange={this.onChange}
          />
        </FormGroup>
      )
    } else {
      return <h4>No batches for this project</h4>
    }
  }
}

BatchSelect.defaultProps = {
  title: 'Batch',
  batches: new List(),
  name: 'batch-select'
};

BatchSelect.propTypes = {
  onChange: PropTypes.func.isRequired,
  batches: ImmutablePropTypes.listOf(batchPropType).isRequired,
  name: PropTypes.string
};

export default BatchSelect;

