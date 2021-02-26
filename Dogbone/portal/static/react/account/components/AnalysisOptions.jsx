import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';

import ToggleActivateButton from './ToggleActivateButton';

import { getAnalysisOptions, toggleAnalysisOption } from '../redux/modules/setting';

// OPTION COMPONENT
const AnalysisOption = ({ option, color, title, active, onToggle }) => {
  return (
    <div className="learners-row">
      {/* static color tag */}
      <div className="btn btn-default learner-color-tag static" style={{ backgroundColor: color }} />
      <span className={`learner-name ${!active ? 'inactive' : ''}`}>
        <span className="learner-label">
          { title }
          <span className="learner-activation">
            <span className="learner-active-btn">
              <ToggleActivateButton
                active={active}
                onClick={() => onToggle(option, active)} />
            </span>
          </span>
        </span>
      </span>
    </div>
  )
};

AnalysisOption.propTypes = {
  option: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  active: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
}

// OPTIONS LIST COMPONENT
class AnalysisOptions extends Component {
  constructor(props) {
    super(props);
    this._toggleOption = this._toggleOption.bind(this);

    this.optionsInOrder = ['responsibilities', 'liabilities', 'terminations', 'external_references'] // list is needed because data is unordered map of flags

    this.info = {
      responsibilities: {
        title: 'Responsibilities',
        color: '#fcd3dd'
      },
      liabilities: {
        title: 'Liabilities',
        color: '#b7dbf3'
      },
      terminations: {
        title: 'Terminations',
        color: '#fcf6b4'
      },
      external_references: {
        title: 'External References',
        color: '#bee1cb'
      }
    }
  }

  componentWillMount() {
    const { dispatch } = this.props;
    dispatch(getAnalysisOptions());
  }

  _toggleOption(option, active) {
    const { dispatch } = this.props;
    dispatch(toggleAnalysisOption(option, !active));
  }

  render() {
    const { options } = this.props;

    return (
      <div className="analysis-options-list">
        { this.optionsInOrder.map((key, i) => (
          <AnalysisOption
            key={i}
            option={key}
            color={this.info[key].color}
            title={this.info[key].title}
            active={options[key]}
            onToggle={this._toggleOption} />
        )) }
      </div>
    )
  }
}

AnalysisOptions.propTypes = {
  options: PropTypes.object
};

const mapStateToProps = state => ({
  options: state.setting.get('analysis_options').toJS()
});

export default connect(mapStateToProps)(AnalysisOptions);