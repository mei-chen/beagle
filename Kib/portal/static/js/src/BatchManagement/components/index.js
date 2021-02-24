import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import BatchManagementPanel from 'BatchManagement/components/BatchManagementPanel';


const AppComponent = () =>
  <div>
    <Grid fluid>
      <Col xs={12} md={12}>
        <h1 id="content-header">
          Batch Management
        </h1>
      </Col>
    </Grid>
    <Grid>
      <Col xs={12} md={12} className="batches-wrapper">
        <BatchManagementPanel />
      </Col>
    </Grid>
  </div>;

export default AppComponent;
