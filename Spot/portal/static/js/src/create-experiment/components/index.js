import React from 'react';
import { connect } from 'react-redux';
import { Grid } from 'react-bootstrap';
import ContentComponent from './ContentComponent';

// App
import 'create-experiment/scss/app.scss';

class AppComponent extends React.Component {
  render() {
    return (
      <Grid fluid={true}>
        <ContentComponent />
      </Grid>
    );
  }
}

AppComponent.defaultProps = {
};

export default connect()(AppComponent);
