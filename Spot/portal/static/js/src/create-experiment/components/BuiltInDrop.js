import React, { Component, PropTypes } from 'react';
import { Form, FormGroup, FormControl, DropdownButton, MenuItem, ButtonGroup, Button } from 'react-bootstrap';

const JURISDICTION = 'Jurisdiction';
const TERMINATION = 'Termination';
const INCLUDE = 'include';
const EXCLUDE = 'exclude';

class BuiltInDrop extends Component {
  constructor(props) {
    super(props)
    this.state = {}
  }

  render() {
    const { apply, type, onChange } = this.props;

    return (
      <Form>
        <FormGroup>
          <div className="wrap-label">Type:</div>
          <div className="wrap-input">
            <DropdownButton title={type} id={type}>
              <MenuItem
                onClick={() => onChange({ model: JURISDICTION }) }>Jurisdiction</MenuItem>
              <MenuItem
                onClick={() => onChange({ model: TERMINATION }) }>Termination</MenuItem>
            </DropdownButton>
          </div>
        </FormGroup>
        <FormGroup>
          <div className="wrap-label">Apply</div>
          <div className="wrap-input">
            <ButtonGroup >
              <Button
                active={apply === INCLUDE}
                onClick={() => { onChange({ apply: INCLUDE }) }}>
                Include
              </Button>
              <Button
                active={apply === EXCLUDE}
                onClick={() => { onChange({ apply: EXCLUDE }) }}>
                Exclude
              </Button>
            </ButtonGroup>
          </div>
        </FormGroup>
      </Form>
    )
  }
}

BuiltInDrop.propTypes = {
  type: PropTypes.oneOf([JURISDICTION, TERMINATION]),
  apply: PropTypes.oneOf([INCLUDE, EXCLUDE]),
  onChange: PropTypes.func.isRequired
}

export default BuiltInDrop;
