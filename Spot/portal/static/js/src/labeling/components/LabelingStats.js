import React, { PropTypes, Component } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import enhanceWithClickOutside from 'react-click-outside';
import BuildExperimentModal from 'labeling/components/BuildExperimentModal';
import uuidV4 from 'uuid/v4';

import { buildExperimentOnServer as buildExperiment } from 'labeling/redux/modules/labeling_module';

class LabelingStats extends Component {
  constructor(props) {
    super(props);
    this._toggleMenu = this._toggleMenu.bind(this);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._buildExperiment = this._buildExperiment.bind(this);

    this.state = {
      showMenu: false,
      showModal: false
    }
  }

  handleClickOutside() {
    this.setState({ showMenu: false });
  }

  _toggleMenu() {
    this.setState({ showMenu: !this.state.showMenu });
  }

  _showModal() {
    this.setState({ showModal: true });
  }

  _hideModal() {
    this.setState({ showModal: false });
  }

  _buildExperiment() {
    const { assignmentId, buildExperiment } = this.props;
    buildExperiment(uuidV4(), assignmentId);
    this.setState({ showModal: true });
  }

  render() {
    const { total, labeled, stage, setTrue, setFalse, setSkipped, currentSamplesCount, isOwner, children } = this.props;
    const { showMenu, showModal } = this.state;

    return (
      <div className="lbl-stats">

        <div className="lbl-stats-left">
          <div className="lbl-stats-progress"><div className="lbl-stats-progress-fill" style={{ width: `${labeled/total*100}%` }}></div></div>
          <div className="lbl-stats-overall">
            Progress:
            <span className="lbl-stats-overall-labeled">{ labeled }</span>
            <span className="lbl-stats-divider">/</span>
            <span className="lbl-stats-overall-total">{ total }</span>
          </div>
        </div>

        <div className="lbl-stats-right">
          <span className="lbl-stats-stage">Stage { stage }</span>

          <div className="lbl-stats-set">
            <span className="lbl-stats-set-labeled">{ setTrue + setFalse }</span>
            (
            <span className="lbl-stats-set-positive">{ setTrue } <i className="fa fa-check-circle" /></span>,
            <span className="lbl-stats-set-negative">{ setFalse } <i className="fa fa-minus-circle" /></span>
            )
            <span className="lbl-stats-divider">/</span>
            <span className="lbl-stats-set-total">{ currentSamplesCount - setSkipped }</span>
            ({ setSkipped } skipped)
          </div>

          <div className="lbl-stats-btn">
            { children }
          </div>

          { isOwner && stage > 1 && (
            <span
              className="lbl-stats-options-trigger"
              onClick={this._toggleMenu} >
              <i className="fa fa-ellipsis-v" />
            </span>
          ) }

          { showMenu && (
            <div className="lbl-stats-menu">
              <span
                className="lbl-stats-menu-option"
                onClick={this._buildExperiment}>Build Experiment</span>
            </div>
          ) }

          <BuildExperimentModal
            show={showModal}
            onHide={this._hideModal} />
        </div>
      </div>
    );
  }
}

LabelingStats.propTypes = {
  assignmentId: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
  labeled: PropTypes.number.isRequired,
  stage: PropTypes.number.isRequired,
  setTrue: PropTypes.number.isRequired,
  setFalse: PropTypes.number.isRequired,
  setSkipped: PropTypes.number.isRequired,
  currentSamplesCount: PropTypes.number.isRequired,
  isOwner: PropTypes.bool.isRequired,
  children: PropTypes.object // button component
};

const mapStateToProps = state => ({});

const mapDispatchToProps = dispatch => bindActionCreators({
  buildExperiment
}, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(enhanceWithClickOutside(LabelingStats));
