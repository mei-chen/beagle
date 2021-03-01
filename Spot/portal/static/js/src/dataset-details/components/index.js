import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid } from 'react-bootstrap';
import Collaborators from 'base/components/Collaborators';

import { DATASET } from 'base/redux/modules/collaborators_module';
import { getFromServer, getSamplesFromServer } from 'dataset-details/redux/modules/dataset_details_module';
import ContentComponent from './ContentComponent';

import 'create-dataset/scss/app.scss';

class AppComponent extends React.Component {
  componentWillMount() {
    const { getFromServer, getSamplesFromServer } = this.props;
    const { id, page } = this.props.params;
    getFromServer(id);
    getSamplesFromServer(id, page);
  }

  render() {
    const { datasetInitialized, samplesInitialized, dataset, params } = this.props;

    if (!datasetInitialized || !samplesInitialized) {
      return (
        <div className="spinner spinner--center" />
      )
    };

    return (
      <Grid fluid={true}>
        <div>
          { +params.id === dataset.get('id') && ( // after we've successfully got dataset with needed id
            <Collaborators
              isOwner={ dataset.get('is_owner') }
              ownerUsername={ dataset.get('owner_username') }
              entity={DATASET}
              id={dataset.get('id')} />
          ) }
          <h1>Dataset Details</h1>
        </div>

        <hr />

        <ContentComponent />
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    datasetInitialized: state.datasetDetailsModule.get('datasetInitialized'),
    samplesInitialized: state.datasetDetailsModule.get('samplesInitialized'),
    dataset: state.datasetDetailsModule.get('dataset')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    getSamplesFromServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
