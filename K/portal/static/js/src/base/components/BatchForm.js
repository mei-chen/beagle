import React from "react";
import PropTypes from "prop-types";
import ImmutablePropTypes from 'react-immutable-proptypes';
import { List } from 'immutable';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { reduxForm } from "redux-form";
import { InputField, SelectField, TextareaField } from 'base/components/FormFields';
import { DefaultButtons } from "base/components/FormControls";
import { getProjects, postProjects } from 'base/redux/modules/projects';
import { FormControl, FormGroup, Button } from 'react-bootstrap';


class BatchForm extends React.Component {
  constructor(props) {
    super(props);
    this.getProjectOptions = this.getProjectOptions.bind(this);
    this.addProjectField = this.addProjectField.bind(this);
    this.createNewProject = this.createNewProject.bind(this);
    this.state = {
      isFieldAdded: false,
      projectName: ''
    }
  }

  getProjectOptions() {
    const options = [];
    this.props.projectStore.every(
      (project) => options.push({ value: project.id, label: project.name })
    );
    return options;
  }

  componentWillMount() {
    if (!this.props.projectStore.size) this.props.getProjects()
  }

  addProjectField() {
    this.setState({ isFieldAdded: true });
  }

  createNewProject() {
    this.props.postProjects({ name: this.state.projectName })
      .then(_ => this.setState({ projectName: '' }))
  }

  render() {
    const { handleSubmit, pristine, submitting, reset, projectAction } = this.props;
    const { isFieldAdded, projectName } = this.state;

    return (
      <form onSubmit={handleSubmit}>
        <InputField
          label="Batch name"
          name="name"
          placeholder="Enter batch name..."
        />

        <SelectField
          label="Project name"
          name={`${projectAction}project`}
          options={this.getProjectOptions()}
          multi
        />

        <FormGroup>
          { !isFieldAdded && (
            <span
              className="optional-field-trigger text-primary"
              onClick={this.addProjectField}>
              + New Project
            </span>
          ) }

          { isFieldAdded && (
            <div>
              <label>Add new project</label>
              <div className="optional-field-wrap">
                <FormControl
                  placeholder="Enter new project name..."
                  onChange={e => this.setState({ projectName: e.target.value })}
                  value={projectName}
                />
                <Button
                  type="button" // important (this button should not submit form)
                  className="optional-field-button"
                  bsStyle="primary"
                  disabled={!projectName}
                  onClick={this.createNewProject}>
                  Add
                </Button>
              </div>
            </div>
          ) }
        </FormGroup>

        <TextareaField
          label="Description"
          name="description"
          placeholder="Enter batch description..."
        />

        <DefaultButtons {...{pristine, submitting, reset, submit_label: 'Create'}} />
      </form>
    )
  }
}

BatchForm.propTypes = {
  projectStore: ImmutablePropTypes.listOf(PropTypes.shape({
    resource_uri: PropTypes.string.isRequired,
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired
  }))
};

BatchForm.defaultProps = {
  projectStore: List(),
  projectAction: 'add_'
};

const form = reduxForm({
  form: 'BatchForm',
  validate(value) {
    const errors = {};
    if (!value.name) errors.name = 'This field is required.';
    return errors
  }
})(BatchForm);

export default connect(
  (state) => ({ projectStore: state.global.projects }),
  (dispatch) => bindActionCreators({ getProjects, postProjects }, dispatch)
)(form);
