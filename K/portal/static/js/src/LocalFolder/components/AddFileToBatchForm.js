import React from "react";
import PropTypes from "prop-types";
import ImmutablePropTypes from 'react-immutable-proptypes';
import { reduxForm } from "redux-form";
import { SelectField } from "base/components/FormFields";
import { DefaultButtons } from "base/components/FormControls";


class AddFileToBatchForm extends React.Component {
  render() {
    const { handleSubmit, batchStore, pristine, submitting, reset } = this.props;
    return (
      <form onSubmit={handleSubmit}>
        <SelectField
          name="batch" label="Select batch"
          options={batchStore.toJS()}
          labelKey="name"
          valueKey="id"
        />
        <DefaultButtons {...{ pristine, submitting, reset, submit_label: 'Add' }} />
      </form>
    )
  }
}

AddFileToBatchForm.propTypes = {
  batchStore: ImmutablePropTypes.listOf(PropTypes.shape({
    resource_uri: PropTypes.string.isRequired,
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired
  }))
};

export default reduxForm({
  form: 'AddFileToBatchForm'
})(AddFileToBatchForm);
