import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import ContentComponent from 'KeyWords/components/ContentComponent';

const AppComponent = () =>
  <div>
    <Grid fluid>
      <Col xs={12} md={12}>
        <h1 id="content-header">
          Key Words
        </h1>
      </Col>
    </Grid>
    <ContentComponent />
  </div>;

export default AppComponent;
