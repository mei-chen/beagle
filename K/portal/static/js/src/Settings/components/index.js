import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import ContentComponent from './ContentComponent';

import 'Settings/scss/app.scss';


const AppComponent = () =>
  <div>
    <Grid fluid>
      <Col xs={12} md={12}>
        <h1 id="content-header">
          Settings
        </h1>
      </Col>
    </Grid>
    <ContentComponent />
  </div>;

export default AppComponent;
