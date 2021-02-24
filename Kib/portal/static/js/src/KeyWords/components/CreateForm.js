import React from "react";
import PropTypes from 'prop-types';
import { reduxForm } from "redux-form";
import { InputField } from "base/components/FormFields";
import { DefaultButtons } from "base/components/FormControls";

import { MODULE_NAME } from 'KeyWords/constants';

class KeywordListCreateForm extends React.Component {
  render() {
    const { handleSubmit, pristine, submitting, reset, submit_label } = this.props;
    let reset_label = 'Cancel';
    return (
      <form onSubmit={handleSubmit}>
        <InputField
          label="Keyword list name"
          name="name"
          placeholder="Enter keyword list name..."
        />
        <DefaultButtons {...{ pristine, submitting, reset, submit_label, reset_label }} />
      </form>
    );
  }
}

KeywordListCreateForm.propTypes = {
  submitLabel: PropTypes.string
};

KeywordListCreateForm.defaultProps = {
  submit_label: 'Create'
};

const initForm = reduxForm({
  form: 'KeywordListCreateForm',
  validate(value) {
    const errors = {};
    if (!value.name) errors.name = 'This field is required.';
    return errors
  }
})(KeywordListCreateForm);

export default initForm;
