import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Button } from 'react-bootstrap';

import { undoHistory, redoHistory, saveCurrentExperimentOnServer } from 'create-experiment/redux/modules/create_experiment_module';

class HistoryButtons extends Component {
    constructor(props) {
        super(props);
        this._handleUndoClick = this._handleUndoClick.bind(this);
        this._handleRedoClick = this._handleRedoClick.bind(this);
        this.state = {}
    }

    _handleUndoClick() {
        const { undoHistory, onClick, saveCurrentExperimentOnServer } = this.props;
        undoHistory();
        saveCurrentExperimentOnServer();
    }

    _handleRedoClick() {
        const { redoHistory, onClick, saveCurrentExperimentOnServer } = this.props;
        redoHistory();
        saveCurrentExperimentOnServer();
    }

    render() {
        const { versionsAmount, formulaVersionsHead } = this.props;
        const canNotUndo = formulaVersionsHead === versionsAmount - 1;
        const canNotRedo = formulaVersionsHead === 0;

        return (
            <div className="history-buttons">
                <Button
                    disabled={canNotUndo}
                    onClick={this._handleUndoClick}>
                    <i className="fa fa-undo" /> undo
                </Button>
                <Button
                    disabled={canNotRedo}
                    onClick={this._handleRedoClick}>
                    <i className="fa fa-redo" /> redo
                </Button>
            </div>
        )
    }
}

const mapStateToProps = (state) => {
  return {
    versionsAmount: state.createExperimentModule.get('formulaVersions').size,
    formulaVersionsHead: state.createExperimentModule.get('formulaVersionsHead')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    undoHistory,
    redoHistory,
    saveCurrentExperimentOnServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(HistoryButtons);
