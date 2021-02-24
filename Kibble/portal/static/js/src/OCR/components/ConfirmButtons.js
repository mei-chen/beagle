import React from "react";
import PropTypes from "prop-types";
import { Button, ButtonToolbar } from "react-bootstrap";

const ConfirmButtons = ({ handleProcessAndReplace, isDisabled, onSaveAsBatchClick }) =>
  <div style={{paddingBottom: 50}}>
    <ButtonToolbar>
      <Button
        bsStyle="danger"
        onClick={handleProcessAndReplace}
        disabled={isDisabled}
      >
        Process and replace
      </Button>
      <Button
        disabled={isDisabled}
        onClick={onSaveAsBatchClick}
      >
        Process and save as batch
      </Button>
    </ButtonToolbar>
  </div>;

ConfirmButtons.propTypes = {
  handleProcessAndReplace: PropTypes.func.isRequired,
  onSaveAsBatchClick: PropTypes.func.isRequired,
  isDisabled: PropTypes.bool.isRequired
};

export default ConfirmButtons;
