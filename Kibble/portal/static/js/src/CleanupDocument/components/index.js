import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import CleanupDocumentPanel from 'CleanupDocument/components/CleanupDocumentPanel';
import 'CleanupDocument/scss/app.scss';

export default () =>
  <div>
    <Grid fluid>
      <Col xs={12} md={12}>
        <h1 id="content-header">
          Cleanup Document
        </h1>
      </Col>
    </Grid>
    <Grid>
      <Col xs={12} md={12}>
        <CleanupDocumentPanel />
      </Col>
    </Grid>
  </div>;
