import React from "react";
import {
  FormGroup,
  ControlLabel,
  FormControl,
  HelpBlock
} from "react-bootstrap";
import { Field } from "redux-form";
import Select from 'react-select';
import 'react-select/dist/react-select.css';


// WRAPPERS
const _getValidationState = ({ touched, error, warning }) => {
  return touched && ( error && "error" ) || ( warning && "warning" ) || null;
};


const _ErrorHelpBlock = ({ meta: { touched, error, warning } }) => {
  const isInvalid = touched && (error || warning);
  return isInvalid ? <HelpBlock>{error}</HelpBlock> : null
};


const _InputComponent = ({ label, meta, input, type, ...rest }) => (
  <FormGroup controlId={input.name}
             validationState={_getValidationState(meta)}>
    { label && <ControlLabel>{label}</ControlLabel> }
    <FormControl type={type} id={input.name} {...input} {...rest} />
    <_ErrorHelpBlock meta={meta}/>
  </FormGroup>
);


const PlainSelect = ({ label, meta, input, type, children, multi, ...rest }) => (
  <FormGroup controlId={input.name}
             validationState={_getValidationState(meta)}>
    { label && <ControlLabel>{label}</ControlLabel> }
    <FormControl componentClass="select" multiple={multi} id={input.name} {...input} {...rest}>
      {children}
    </FormControl>
    <_ErrorHelpBlock meta={meta}/>
  </FormGroup>
);


class ReactSelect extends React.Component {
  constructor(props) {
    super(props);
    this.valueKey = this.props.valueKey || 'value';
    this.onChange = this.onChange.bind(this);
  }

  onChange(ev) {
    const input = this.props.input;
    if (input.onChange) {
      let selected;
      // Array if multi select, object if single, null on delete
      const isArray = Array.isArray(ev);
      if (isArray) {
        selected = [];
        ev.every(el => selected.push(el[this.valueKey]))
      } else if (!isArray && ev !== null) {
        selected = ev[this.valueKey];
      }
      input.onChange(selected);
    }
  }

  render() {
    const { label, meta, input, options, multi } = this.props;
    return (
      <FormGroup controlId={input.name} validationState={_getValidationState(meta)}>
        { label && <ControlLabel>{label}</ControlLabel> }
        <Select.Creatable
          {...this.props}
          value={input.value || ''}
          onBlur={() => input.onBlur(input.value)}
          onChange={this.onChange}
          options={options}
          multi={multi}
        />
        <_ErrorHelpBlock meta={meta}/>
      </FormGroup>
    );
  }
}
// --------------------------


// FIELDS
const InputField = ({ label, name, placeholder }) => (
  <Field
    type="text"
    component={_InputComponent}
    label={label}
    name={name}
    placeholder={placeholder || name}
  />
);


const TextareaField = ({ label, name, placeholder }) => (
  <Field
    componentClass="textarea"
    component={_InputComponent}
    label={label}
    name={name}
    placeholder={placeholder || name}
  />
);


const SelectField = ({ label, name, options, multi, ...rest }) =>
  <Field
    component={props => <ReactSelect {...props} options={options} multi={multi} {...rest} />}
    label={label}
    name={name}
  />;


SelectField.defaultProps = {
  multi: false,
  label: ''
};
// --------------------------

export { InputField, SelectField, TextareaField };
