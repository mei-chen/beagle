import React from "react";
import { connect } from 'react-redux';
import { reduxForm } from "redux-form";
import { InputField } from "base/components/FormFields";
import { DefaultButtons } from "base/components/FormControls";
import { MODULE_NAME } from 'ProjectManagement/constants';

class ProjectForm extends React.Component {
  render() {
    const { handleSubmit, pristine, submitting, reset } = this.props;
    return (
      <form onSubmit={handleSubmit}>
        <InputField
          label="Project name"
          name="name"
          placeholder="Enter project name..."
        />
        <DefaultButtons {...{ pristine, submitting, reset }} />
      </form>
    );
  }
}

const initForm = reduxForm({
  form: 'ProjectForm',
  validate(value) {
    const errors = {};
    if (!value.name) errors.name = 'This field is required.';
    return errors
  }
})(ProjectForm);

export default connect(
  state => {
    return { initialValues: state[ MODULE_NAME ].get('selectedProject').toJS() }
  }
)(initForm);
