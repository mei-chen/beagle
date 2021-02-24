import React from "react";
import { Button, ButtonToolbar } from "react-bootstrap";


const DefaultButtons = ({
  pristine,
  submitting,
  reset,
  float='right',
  submit_label='Send',
  reset_label='Reset'
}) => (
  <ButtonToolbar>
    <Button type="submit" bsStyle="primary" style={{float}}
            disabled={pristine || submitting}>
      {submit_label}
    </Button>

    <Button type="reset" disabled={pristine || submitting}
            onClick={reset} style={{float}}>
      {reset_label}
    </Button>
  </ButtonToolbar>
);

export { DefaultButtons };
