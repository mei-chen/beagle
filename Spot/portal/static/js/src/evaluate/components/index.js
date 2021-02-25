import React from 'react';
import { Link } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';

// App
import { getFromServer as getExperimentFromServer } from 'create-experiment/redux/modules/create_experiment_module';
import ContentComponent from './ContentComponent';

import 'evaluate/scss/app.scss';


class AppComponent extends React.Component {
  componentDidMount() {
    const { getExperimentFromServer, experimentName } = this.props;
    const { id:experimentId } = this.props.params;
    if(!experimentName) getExperimentFromServer(experimentId);
  }

  render() {
    const { experimentName } = this.props;
    const { id:experimentId } = this.props.params;

    return (
      <Grid fluid={true}>
        <h1 className="title">
          <Link className="link-back" to={`/experiments/${experimentId}/edit`}>
            <i className="fa fa-chevron-left" />
          </Link>
          <span>Evaluate</span>
          <span className="gray-label">{ experimentName }</span>
        </h1>

        <hr />

        <ContentComponent />
      </Grid>
    );
  }
}

AppComponent.defaultProps = {
};

const mapStateToProps = (state) => {
  return {
    experimentName: state.createExperimentModule.get('name')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getExperimentFromServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
