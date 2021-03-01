import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import uuidV4 from 'uuid/v4';
import Classifier from './Classifier';

class ClassifiersList extends Component {
  constructor(props) {
    super(props)
    this._renderExperiment = this._renderExperiment.bind(this);
    this.state = {}
  }

  _renderExperiment(formula) {
    const { trainingErrors, confidenceById } = this.props;

    return formula.map((item, i) => {
      const classifier = item.get('classifier');
      const weight = item.get('weight');
      const uuid = item.get('uuid');

      return (
        <Classifier
        key={uuid || uuidV4()}
        uuid={uuid}
        index={i}
        weight={weight}
        classifier={classifier}
        trainingError={trainingErrors.get(uuid)}
        confidence={confidenceById.get(uuid)} />
      )
    })
  }

  render() {
    const { formula } = this.props;

    return (
      <div className="classifiers-list">
        {this._renderExperiment(formula)}
      </div>
    )
  }
}

ClassifiersList.propTypes = {
    // prop: PropTypes.string.isRequired
}

const mapStateToProps = state => {
  return {
    formula: state.createExperimentModule.get('formula'),
    trainingErrors: state.createExperimentModule.get('trainingErrors'),
    confidenceById: state.createExperimentModule.get('confidenceById')
  }
};


export default connect(mapStateToProps)(ClassifiersList);
