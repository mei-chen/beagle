import React, { Component } from 'react';
import { Grid } from 'react-bootstrap';
import DatasetDetails from './DatasetDetails';
import SamplesTable from './SamplesTable';

import 'dataset-details/scss/app.scss';

class ContentComponent extends Component {
  render() {
    return (
      <div>
        <DatasetDetails />
        <SamplesTable />
      </div>
    );
  }
}

export default ContentComponent;
