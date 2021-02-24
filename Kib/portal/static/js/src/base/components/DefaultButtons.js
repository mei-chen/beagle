import React from 'react';
import {
  ButtonGroup,
  Button
} from 'react-bootstrap';


const style = {
  marginBottom: 10
};

export const SwitchSelectState = ({ onSelectAll, onDeselectAll }) => (
  <ButtonGroup style={style}>
    <Button onClick={onSelectAll}>
      Select all
    </Button>
    <Button onClick={onDeselectAll}>
      Deselect all
    </Button>
  </ButtonGroup>
);
