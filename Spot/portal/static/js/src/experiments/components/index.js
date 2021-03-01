import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid } from 'react-bootstrap';

// App
import { getFromServer } from 'experiments/redux/modules/experiments_module';
import ContentComponent from './ContentComponent';
import 'experiments/scss/app.scss';


class AppComponent extends React.Component {
  componentDidMount() {
    this.props.getFromServer();
  }

  render() {
    const { isInitialized, user } = this.props;

    if (!isInitialized) {
      return (
        <div className="spinner spinner--center" />
      )
    };

    return (
      <Grid fluid={true}>
        <h1 className="title">Experiments</h1>

        <hr />

        <ContentComponent />
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    isInitialized: state.experimentsModule.get('isInitialized'),
    user: state.user
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
