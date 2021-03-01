import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { List } from 'immutable';
import Learner from './Learner';

class LearnersList extends Component {
  constructor(props) {
    super(props)
    this._renderLearners = this._renderLearners.bind(this);
    this.state = {}
  }

  _renderLearners(learners) {
    return learners.map((learner, i) => {
      return (
        <Learner
          key={i}
          learner={learner} />
      )
    })
  }

  render() {
    const { learners } = this.props;

    if(!learners || learners.size === 0) return null;

    return (
      <div className="learners-list">
        {this._renderLearners(learners)}
      </div>
    )
  }
}

LearnersList.propTypes = {
    learners: PropTypes.instanceOf(List)
}

const mapStateToProps = state => {
  return {
    learners: state.createExperimentModule.get('learners')
  }
};

export default connect(mapStateToProps)(LearnersList);
