import React, { Component, PropTypes } from 'react';
import { Form, FormGroup, FormControl, ButtonGroup, Button } from 'react-bootstrap';

const INCLUDE = 'include';
const EXCLUDE = 'exclude';

class RegexDrop extends Component {
  constructor(props) {
    super(props)
    this.state = {}
  }

  render() {
    const { apply, regex, isValidRegex, onChange } = this.props;

    return (
      <Form>
        <FormGroup>
          <div className="wrap-label">Expression</div>
          <div className="wrap-input">
            <FormControl
              type="text"
              placeholder="Regex"
              onChange={(e) => { onChange({ expression: e.target.value }) }}
              defaultValue={regex} />
            { !isValidRegex && (
              <span className="text-danger">Regex is not valid</span>
            ) }
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

RegexDrop.propTypes = {
  regex: PropTypes.string.isRequired,
  isValidRegex: PropTypes.bool.isRequired,
  apply: PropTypes.oneOf([INCLUDE, EXCLUDE]),
  onChange: PropTypes.func.isRequired
}

export default RegexDrop;
