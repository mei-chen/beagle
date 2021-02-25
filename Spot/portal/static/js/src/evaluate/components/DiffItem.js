import React, { Component, PropTypes } from 'react';
import { Map } from 'immutable';
import { connect } from 'react-redux';
import Progress from 'base/components/Progress';
import SimulateResult from 'create-experiment/components/SimulateResult';
import SimulateStatus from 'create-experiment/components/SimulateStatus';

import { simulateDiffOnServer } from 'evaluate/redux/modules/diff_module';

class DiffItem extends Component {
  constructor(props) {
    super(props);
    this._toggleDrop = this._toggleDrop.bind(this);
    this._renderResults = this._renderResults.bind(this);
    this.state = {
      isOpen: false
    }
  }

  _toggleDrop() {
    const { isOpen } = this.state;
    const { onSimulate, simulation } = this.props;

    if(!isOpen) {
      !simulation && onSimulate();
      this.setState({ isOpen: true });
    } else {
      this.setState({ isOpen: false });
    }
  }

  _renderResults(results) {
    return results.map((result, i) => (
      <SimulateResult
        key={i}
        name={result.get('name')}
        type={result.get('type')}
        weight={result.get('weight')}
        sample={result.get('sample')}
        status={result.get('status')} />
    ));
  }

  render() {
    const { droppable, gold, text, label, simulation } = this.props;
    const { isOpen } = this.state;
    const iconClass = isOpen ? 'fa fa-arrow-alt-to-top' : 'fa fa-arrow-alt-from-top';

    return (
      <div className="diff-item">
        <div className="diff-item-body clearfix">
          <div className={`dataset-preview-gold ${ gold === true ?  'dataset-preview-gold--pos' : 'dataset-preview-gold--neg' }`}>
            <i className="fa fa-times" />
          </div>
          <div className={`dataset-preview-item dataset-preview-item--has-icon ${ label === true ? 'dataset-preview-item--pos' : 'dataset-preview-item--neg' }`}>
            { text }

            <div className="dataset-preview-item-icons">
              <i
                className={iconClass}
                onClick={this._toggleDrop} />
            </div>
          </div>
        </div>

        { isOpen && (
          <div className="diff-item-drop">
            { !simulation || simulation.get('isSimulating') ? (
              <i className="fa fa-spinner fa-pulse fa-fw" />
            ) : (
              <div>
                <div className="diff-item-info">
                  <div className="status-wrap">
                    <SimulateStatus status={simulation.get('status')} />
                  </div>

                  <div className="confidence-wrap">
                    <strong>Confidence: </strong><Progress value={simulation.get('confidence')} />
                  </div>
                </div>

                { simulation.get('status') === true && (
                  <div className="diff-item-results">
                    <div className="diff-item-main-result">
                      <SimulateResult
                        short={true}
                        sample={simulation.get('sample')} />
                    </div>
                    { simulation.get('resultsPerClassifier') && (
                      <div className="diff-item-detailed-results">
                        { this._renderResults(simulation.get('resultsPerClassifier')) }
                      </div>
                    ) }
                  </div>
                ) }
              </div>
            ) }
          </div>
        ) }
      </div>
    )
  }
}

DiffItem.propTypes = {
  gold: PropTypes.bool.isRequired,
  text: PropTypes.string.isRequired,
  label: PropTypes.bool.isRequired,
  onSimulate: PropTypes.func,
  simulation: PropTypes.instanceOf(Map)
};

const mapStateToProps = (state, ownProps) => {
  return {
    simulation: state.diffModule.get('diffSimulations').get(ownProps.simulationTaskUuid)
  }
}

export default connect(mapStateToProps)(DiffItem);
