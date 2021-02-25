import React from 'react';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';

// App
import ContentComponent from './ContentComponent';

import 'create-dataset/scss/app.scss';

class AppComponent extends React.Component {
  render() {
    return (
      <div>
        <ContentComponent />
      </div>
    );
  }
}

AppComponent.defaultProps = {
};

export default connect()(AppComponent);
