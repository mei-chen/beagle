import React from 'react';
import pt from 'prop-types';
import { Panel, Button, Grid, Col, ButtonToolbar } from 'react-bootstrap';


const RegExPanel = ({ setModalOpen, selectedRegEx }) =>
  <Panel>
    <Grid>
      <Col xs={12} md={12}>
        <ButtonToolbar>
          <Button
            bsSize="small"
            onClick={() => setModalOpen('create', true)}
          >
            Create New RegEx
          </Button>
          <Button
            bsSize="small"
            onClick={() => setModalOpen('edit', true)}
            disabled={!selectedRegEx.size}
          >
            Edit RegEx
          </Button>
          <Button
            bsSize="small"
            bsStyle="danger"
            onClick={() => setModalOpen('delete', true)}
            disabled={!selectedRegEx.size}
          >
            Delete RegEx
          </Button>
        </ButtonToolbar>
      </Col>
    </Grid>
  </Panel>;

RegExPanel.propTypes = {
  setModalOpen: pt.func
};

export default RegExPanel;
