/**
 * For using outside forms
 */
import React from "react";
import PropTypes from "prop-types";
import {
  FormGroup,
  ControlLabel,
  FormControl,
  HelpBlock
} from "react-bootstrap";


// Fields
export const UInputField = ({ id, label, name, ...props }) => (
  <FormGroup controlId={id}>
    <ControlLabel>{label}</ControlLabel>
    <FormControl name={name} {...props} />
  </FormGroup>
);

export const USelectField = ({ id, label, name, children, ...props }) => (
  <FormGroup controlId={id}>
    <ControlLabel>{label}</ControlLabel>
    <FormControl name={name} componentClass="select" {...props} >
      <option value="">----</option>
      {children}
    </FormControl>
  </FormGroup>
);

export const UFileField = ({ id, name, help, ...props }) => (
  <FormGroup controlId={id}>
    <input
      type="file"
      name={name}
      id={`${id}-${name}`}
      {...props}
    />
    { help && <HelpBlock>{help}</HelpBlock> }
  </FormGroup>
);
// --------


// propTypes
UInputField.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired
};
USelectField.propTypes = {
  label: PropTypes.string.isRequired,
  children: PropTypes.node,
  name: PropTypes.string.isRequired
};
UFileField.propTypes = {
  label: PropTypes.string,
  name: PropTypes.string.isRequired,
  help: PropTypes.string
};
// --------
