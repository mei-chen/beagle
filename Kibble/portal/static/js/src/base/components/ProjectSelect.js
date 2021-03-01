import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { FormGroup, ControlLabel } from 'react-bootstrap';
import { projectPropType } from "ProjectManagement/propTypes";
import { convertObjectsToOptions } from 'base/utils/misc';
import Select from 'react-select';
import 'react-select/dist/react-select.css';


export const PROJECT_NOT_SELECTED = -1;
export const PROJECT_ALL = 0;


class ProjectSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      option: this.props.preSelected
    };
    this.onChange = this.onChange.bind(this);
    this.getOptions = this.getOptions.bind(this);
  }

  getOptions() {
    const { displayAllOption } = this.props;
    const options = displayAllOption ? [{ value: PROJECT_ALL, label: 'All' }] : [];
    this.props.projectStore.every((project) => options.push({ value: project.id, label: project.name }));
    return options
  }

  onChange(option) {
    this.setState({ option });
    this.props.onChange(option ? option.value : PROJECT_NOT_SELECTED)
  }

  render() {
    return (
      <FormGroup>
        <ControlLabel>{ this.props.title }</ControlLabel>
        <Select
          name="project-select"
          value={this.state.option}
          options={this.getOptions()}
          onChange={this.onChange}
        />
      </FormGroup>
    )
  }
}

ProjectSelect.defaultProps = {
  title: 'Project',
  displayAllOption: true
};

ProjectSelect.propTypes = {
  onChange: PropTypes.func.isRequired,
  projectStore: PropTypes.arrayOf(projectPropType).isRequired,
  displayAllOption: PropTypes.bool
};

export default connect(
  (state) => ({ projectStore: state.global.projects.toJS() }),
)(ProjectSelect)
