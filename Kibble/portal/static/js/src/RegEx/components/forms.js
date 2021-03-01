import React from "react";
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { reduxForm } from 'redux-form';
import { ButtonToolbar, ButtonGroup, Button, ToggleButtonGroup, ToggleButton, DropdownButton, MenuItem, FormGroup, FormControl, ControlLabel, Form } from 'react-bootstrap'
import { InputField } from "base/components/FormFields";
import { DefaultButtons } from "base/components/FormControls";

import { MODULE_NAME } from 'RegEx/constants';

class RegExForm extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      auto_regex: false,
      name: this.props.name,
      regex: this.props.content,
      word1: '',
      word2: '',
      count1: '',
      count2: '',
      case_sensitive: [],
      logic_op: []
    }
    this.switchRegexMode = this.switchRegexMode.bind(this);
    this.onSensitiveChange = this.onSensitiveChange.bind(this);
    this.onLogicOpChange = this.onLogicOpChange.bind(this);
    this.onNameChange = this.onNameChange.bind(this);
    this.onRegexChange = this.onRegexChange.bind(this);
    this.onWord1Change = this.onWord1Change.bind(this);
    this.onWord2Change = this.onWord2Change.bind(this);
    this.handleFormSubmit = this.handleFormSubmit.bind(this);
    this.onCount1Change = this.onCount1Change.bind(this);
    this.onCount2Change = this.onCount2Change.bind(this);
  }

  switchRegexMode(){
    this.setState({auto_regex: !this.state.auto_regex})
  }

  onSensitiveChange(e){
    this.setState({ case_sensitive: e});
  };

  onLogicOpChange(e){
    this.setState({ logic_op: e});
    console.log(e);
  };

  onNameChange(e){
    this.setState({name: e.target.value});
  }

  onRegexChange(e){
    this.setState({regex: e.target.value});
  }

  onWord1Change(e){
    this.setState({word1: e.target.value});
  }

  onWord2Change(e){
    this.setState({word2: e.target.value});
  }

  onCount1Change(e){
    this.setState({count1: e.target.value});
  }

  onCount2Change(e){
    this.setState({count2: e.target.value});
  }

  handleFormSubmit(evt) {
    evt.preventDefault();
    var content = '';
    const { case_sensitive, word1, logic_op, word2, auto_regex, name, regex, count1, count2 } = this.state;

    if (auto_regex){
      //case sensitive button is not hit
      if (case_sensitive.length === 0)
        content += '(?i)';

      if(logic_op === 1)
        content = content + "^(?=.*\\b" + word1 + "\\b)(?=.*\\b" + word2 + "\\b).*$";
      else if (logic_op === 2)
        content = content + word1 + "|" + word2;
      else if (logic_op === 3)
        content = content + word1 + `(\\s*([a-zA-Z0-9.\\]\\[,]+)\\s*){${count1},${count2}}` + word2
    } else {
      content = regex;
    }
    console.log(content);
    this.props.onSubmit({name:name,content:content})
  }

  render() {
    const { handleSubmit, onClose, pristine, submitting, reset, submit_label, name, content } = this.props;
    let reset_label = 'Cancel';
    return (
      <form onSubmit={this.handleFormSubmit}>
        <FormGroup controlId="formBasicTextt">
          <ControlLabel>RegEx name</ControlLabel>
          <FormControl
            value={this.state.name}
            type="text"
            placeholder="Enter regex name..."
            onChange={this.onNameChange}
          />
        </FormGroup>
        {submit_label === 'Create' &&
          <FormGroup controlId="regexMode">
            <ButtonToolbar>
              <ButtonGroup bsSize="small">
                <Button disabled={this.state.auto_regex ? false : true} onClick={this.switchRegexMode} >Manual RegEx</Button>
                <Button disabled={this.state.auto_regex ? true : false} onClick={this.switchRegexMode} >Auto RegEx</Button>
              </ButtonGroup>
            </ButtonToolbar>
          </FormGroup>
        }

        {this.state.auto_regex ? 
          <span>
            <FormGroup controlId="formBasicTextt">
              <ControlLabel>Auto RegEx</ControlLabel>
              <FormControl
                type="text"
                placeholder="Enter first word..."
                onChange={this.onWord1Change}
              />
            </FormGroup>
            <FormGroup controlId="regexOps">
              <ButtonToolbar>
                <ToggleButtonGroup type="checkbox" name="Case sensitive" bsSize="small" onChange={this.onSensitiveChange}>
                  <ToggleButton value={1}>Aa</ToggleButton>
                </ToggleButtonGroup>
                <ToggleButtonGroup type="radio" name="options" defaultValue={1} bsSize="small" onChange={this.onLogicOpChange}>
                  <ToggleButton value={1}>AND</ToggleButton>
                  <ToggleButton value={2}>OR</ToggleButton>
                  <ToggleButton value={3}>Words in between</ToggleButton>
                </ToggleButtonGroup>
              </ButtonToolbar>
            </FormGroup>
            {this.state.logic_op === 3 &&
              <div>
                {"  from "}
                <FormGroup controlId="regexOps" style={{display : 'inline-block'}}>
                  <FormControl type="text" style={{width:"50px"}} onChange={this.onCount1Change}/>
                </FormGroup>
                {"  to "}
                <FormGroup controlId="regexOps" style={{display : 'inline-block'}}>
                  <FormControl type="text" style={{width:"50px"}} onChange={this.onCount2Change}/>
                </FormGroup>
                {"  words in between"}
              </div>
            }
            <FormGroup controlId="formBasicText">
              <FormControl
                type="text"
                placeholder="Enter second word"
                onChange={this.onWord2Change}
              />
            </FormGroup>
          </span> :
          <FormGroup controlId="formBasicTextt">
            <ControlLabel>RegEx</ControlLabel>
            <FormControl
              value={this.state.regex}
              type="text"
              placeholder="Enter regex..."
              onChange={this.onRegexChange}
            />
          </FormGroup>
        }
        <ButtonToolbar>
          <Button type="reset" onClick={onClose}>Cancel</Button>
          <Button bsStyle="primary" type="submit">{`${submit_label === 'Create' ? "Create" : "Update"}`}</Button>
        </ButtonToolbar>
      </form>
    );
  }
}

RegExForm.propTypes = {
  submitLabel: PropTypes.string
};

RegExForm.defaultProps = {
  submit_label: 'Create'
};

const initForm = reduxForm({
  form: 'RegExForm',
  validate(value) {
    const errors = {};
    if (!value.name) errors.name = 'This field is required.';
    if (!value.content) errors.content = 'This field is required.';
    if (!value.word1) errors.word1 = 'This field is required.';
    if (!value.word2) errors.word2 = 'This field is required.';
    return errors
  }
})(RegExForm);

export default connect(
  state => {
    return { initialValues: state[ MODULE_NAME ].get('selectedRegEx').toJS() }
  }
)(initForm);
