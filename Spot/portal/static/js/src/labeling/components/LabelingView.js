import React, { Component, PropTypes } from 'react';
import { Map, List, toJS } from 'immutable';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Button, Alert } from 'react-bootstrap';
import uuidV4 from 'uuid/v4';
import LabelingTable from 'labeling/components/LabelingTable';
import LabelingStats from 'labeling/components/LabelingStats';

import {
  getAssignmentFromServer as getAssignment,
  getSamplesFromServer as getSamples,
  postSamplesToServer as postSamples,
  setLabel,
  setSkipped
} from 'labeling/redux/modules/labeling_module';

class LabelingView extends Component {
  constructor(props) {
    super(props);
    this._getData = this._getData.bind(this);
    this._postData = this._postData.bind(this);
  }

  componentWillMount() {
    this._getData();
  }

  _getData() {
    const { getAssignment, getDataset, getSamples } = this.props;
    const { id:assignmentId } = this.props.params;

    getAssignment(assignmentId)
      .then(res => getSamples(uuidV4(), assignmentId));
  }

  _postData() {
    const { samples, postSamples } = this.props;
    const { id:assignmentId } = this.props.params;

    // remove 'skipped' field that is not needed on back-end
    const preparedData = samples.get('data').map(sample => sample.remove('skipped')).toJS();
    postSamples(uuidV4(), assignmentId, preparedData) // new data will be get after this process ends
  }

  _isNextStageAllowed(samples) {
    // if there are not labeled or not skipped samples
    return !!samples.find(sample => typeof sample.get('label') === 'undefined' && !sample.get('skipped'));
  }

  render() {
    const { user, samples, assignment, stage, stats, setLabel, setSkipped } = this.props;
    const isNextStageAllowed = this._isNextStageAllowed(samples.get('data'));

    if(samples.get('isLoading') || assignment.get('isLoading')) return <div className="spinner spinner--center" />;

    return (
      <Grid fluid>
        <h1>Labeling assignment</h1>
        <hr />

        {/* heading */}
        { !assignment.get('data').isEmpty() && (
          <div className="card">
            <div className="card-item">
              <h3>{ assignment.get('data').get('labeling_task').get('name') }</h3>
            </div>
            <div className="card-item">{ assignment.get('data').get('labeling_task').get('description') }</div>
          </div>
        ) }

        {/* samples */}
        { samples.get('data').size > 0 ? (
          <LabelingTable
            samples={samples.get('data')}
            stage={stage}
            onSet={(index, label) => setLabel(index, label)}
            onSkip={index => setSkipped(index)} />
        ) : (
          <Alert bsStyle="success">You are done!</Alert>
        ) }

        {/* next */}
        { samples.get('data').size > 0 && (
          <div>
            <LabelingStats
              assignmentId={assignment.get('data').get('id')}
              stage={stage}
              total={stats.get('total')}
              labeled={stats.get('labeled')}
              setTrue={samples.get('data').filter(s => s.get('label') === true).size}
              setFalse={samples.get('data').filter(s => s.get('label') === false).size}
              setSkipped={samples.get('data').filter(s => s.get('skipped')).size}
              currentSamplesCount={samples.get('data').size}
              isOwner={user.get('id') === assignment.get('data').get('owner').get('id')}>

              <Button
                bsStyle="primary"
                disabled={isNextStageAllowed}
                onClick={this._postData}>
                Next >
              </Button>

            </LabelingStats>
          </div>
        ) }
      </Grid>
    )
  }
}

LabelingView.propTypes = {
  stage: PropTypes.number, // could be null
  samples: PropTypes.instanceOf(Map).isRequired,
  assignment: PropTypes.instanceOf(Map).isRequired,
  stats: PropTypes.instanceOf(Map).isRequired
};

const mapStateToProps = state => ({
  user: state.user.get('details'),
  stage: state.labelingModule.get('stage'),
  samples: state.labelingModule.get('samples'),
  assignment: state.labelingModule.get('assignment'),
  stats: state.labelingModule.get('stats')
});

const mapDispatchToProps = dispatch => (
  bindActionCreators({
    getAssignment,
    getSamples,
    postSamples,
    setLabel,
    setSkipped
  }, dispatch)
);

export default connect(mapStateToProps, mapDispatchToProps)(LabelingView);
