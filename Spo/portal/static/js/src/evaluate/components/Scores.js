import React, { Component, PropTypes } from 'react';
import { Map } from 'immutable';
import { connect } from 'react-redux';
import { Table } from 'react-bootstrap';
import ScoresList from 'base/components/ScoresList';

class Scores extends Component {
  constructor(props) {
    super(props);
    this.state = {}
  }

  render() {
    const { scores } = this.props;

    if(scores.size > 0) {
      return (
        <div className="scores">
          <h3>Scores</h3>
          <ScoresList 
            f1={scores.get('f1')}
            precision={scores.get('precision')}
            recall={scores.get('recall')}
          />
        </div>
      )
    }

    return null;
  }
}

Scores.propTypes = {
  scores: PropTypes.instanceOf(Map),
}

const mapStateToProps = (state) => {
  return {
    scores: state.evaluateModule.get('scores'),
  }
};

export default connect(mapStateToProps)(Scores);
