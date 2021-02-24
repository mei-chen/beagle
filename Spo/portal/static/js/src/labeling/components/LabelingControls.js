import React, { Component, PropTypes } from 'react';

class LabelingControls extends Component {
  constructor(props) {
    super(props);
    this.state = {
      label: null
    }
  };

  render() {
    const { label, skipped, onSet, onSkip, onChange, skipButton, changeButton } = this.props;

    return (
      <div className={`lbl-controls ${skipped ? 'lbl-controls--skipped' : ''}`}>
        <span
          className={`lbl-control ${label === true ? 'lbl-control--true' : ''}`}
          onClick={() => onSet(true)}>
          <i className="fa fa-check-circle" />
          <span>True</span>
        </span>

        <span
          className={`lbl-control ${label === false ? 'lbl-control--false' : ''}`}
          onClick={() => onSet(false)}>
          <i className="fa fa-minus-circle" />
          <span>False</span>
        </span>

        { skipButton && (
          <span
            className={`lbl-skip ${skipped ? 'lbl-skip--skipped' : ''}`}
            onClick={() => onSkip(!skipped)}>
            { skipped && <i className="fa fa-exclamation-triangle" /> }
            <span>{ skipped ? 'Skipped' : 'Skip' }</span>
          </span>
        ) }

        { changeButton && (
          <span
            className="lbl-change"
            onClick={() => onChange()}>
            <span><i className="fa fa-redo" /> Change</span>
          </span>
        ) }
      </div>
    );
  }
}

LabelingControls.propTypes = {
  label: PropTypes.bool, // could be undefined
  skipped: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onSkip: PropTypes.func.isRequired,
  skipButton: PropTypes.bool,
  changeButton: PropTypes.bool
};

LabelingControls.defaultProps = {
  label: undefined,
  skipped: false
};

export default LabelingControls;
