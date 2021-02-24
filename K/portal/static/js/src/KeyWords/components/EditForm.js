import React from "react";
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { reduxForm } from "redux-form";
import { InputField, SelectField } from "base/components/FormFields";
import { DefaultButtons } from "base/components/FormControls";

import { MODULE_NAME } from 'KeyWords/constants';

class KeywordListEditForm extends React.Component {
  constructor(props) {
    super(props);
    this.getKeywordsOption = this.getKeywordsOption.bind(this);
  }

  getKeywordsOption() {
    const options = [];
    this.props.initialValues.keywords.every(
      keyword => options.push({ value: keyword.uuid, label: keyword.content })
    );
    return options;
  }

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
        <SelectField
          label="Keywords"
          name="keywords"
          labelKey="content"
          valueKey="uuid"
          options={this.props.initialValues.keywords}
          multi
        />
        <DefaultButtons {...{ pristine, submitting, reset, submit_label, reset_label }} />
      </form>
    );
  }
}

KeywordListEditForm.propTypes = {
  submitLabel: PropTypes.string
};

KeywordListEditForm.defaultProps = {
  submit_label: 'Edit'
};

const initForm = reduxForm({
  form: 'KeywordListEditForm',
  validate(value) {
    const errors = {};
    if (!value.name) errors.name = 'This field is required.';
    return errors
  }
})(KeywordListEditForm);

export default connect(
  state => {
    return { initialValues: state[ MODULE_NAME ].get('selectedKeywordList').toJS() }
  }
)(initForm);
