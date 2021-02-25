import React from 'react';
import { Grid, Col } from 'react-bootstrap';

// App
import { MODULE_NAME } from 'RegEx/constants';
import ContentComponent from 'RegEx/components/ContentComponent';


export default () =>
  <div>
    <Grid fluid>
      <Col xs={12} md={12}>
        <h1 id="content-header">
          Regular expressions
        </h1>
      </Col>
    </Grid>
    <ContentComponent />
  </div>;
