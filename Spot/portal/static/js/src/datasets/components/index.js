import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';

// App
import { getFromServer } from 'datasets/redux/modules/datasets_module';
import ContentComponent from './ContentComponent';

import 'datasets/scss/app.scss';


class AppComponent extends React.Component {
  componentDidMount() {
    this.props.getFromServer();
  }

  render() {
    const { isInitialized } = this.props;

    if (!isInitialized) {
      return (
        <div className="spinner spinner--center" />
      )
    };

    return (
      <Grid fluid={true}>
        <h1>Datasets</h1>

        <hr />

        <ContentComponent />
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    isInitialized: state.datasetsModule.get('isInitialized')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
