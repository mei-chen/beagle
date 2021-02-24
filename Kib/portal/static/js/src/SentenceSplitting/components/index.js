import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import ContentComponent from './ContentComponent';


const AppComponent = () =>
  <div>
    <Grid fluid>
      <Col xs={12} md={12}>
        <h1 id="content-header">
          Sentence Splitting
        </h1>
      </Col>
    </Grid>
    <Grid>
      <Col xs={12} md={12}>
        <ContentComponent />
      </Col>
    </Grid>
  </div>;


export default AppComponent;
