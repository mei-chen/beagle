import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import uuidV4 from 'uuid/v4';
import { ControlLabel, FormGroup, FormControl, Button, Alert } from 'react-bootstrap';
import Progress from 'base/components/Progress';
import SimulateResult from './SimulateResult';
import SimulateStatus from './SimulateStatus';

import { simulateOnServer } from 'create-experiment/redux/modules/simulate_module';

class Simulate extends Component {
    constructor(props) {
        super(props)
        this._handleChange = this._handleChange.bind(this);
        this._handleButtonClick = this._handleButtonClick.bind(this);
        this._renderResults = this._renderResults.bind(this);
        this._toggleDrop = this._toggleDrop.bind(this);
        this.state = {
            text: '',
            dirty: false,
            isOpen: false
        }
    }

    componentWillReceiveProps(nextProps) {
        if(this.props.status !== nextProps.status) {
            this.setState({ dirty: false })
        }
    }

    _handleChange(e) {
        this.setState({ text: e.target.value, dirty: true });
    }

    _handleButtonClick() {
        const { simulateOnServer, id } = this.props;
        simulateOnServer( uuidV4(), id, this.state.text );
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

    _toggleDrop() {
        this.setState({ isOpen: !this.state.isOpen });
    }

    render() {
        const { text, dirty, isOpen } = this.state;
        const { status, sample, resultsPerClassifier, confidence, errorMessage, isSimulating, isSimulatedFormulaDirty } = this.props;
        const canNotBeClassified = !text.trim();
        const enableButton = dirty || isSimulatedFormulaDirty;
        const isDropContent = !!resultsPerClassifier && resultsPerClassifier.size > 0;
        const iconClass = isOpen ? 'fa fa-arrow-alt-to-top' : 'fa fa-arrow-alt-from-top';

        if(errorMessage) {
            return <Alert bsStyle="warning">{ errorMessage }</Alert>
        }

        return (
            <div className="simulate">
                {/* form */}
                <div className="simulate-form clearfix">
                    <FormGroup className="simulate-input">
                        <FormControl
                            disabled={isSimulating}
                            className="simulate-textarea"
                            componentClass="textarea"
                            value={text}
                            onChange={this._handleChange} />
                    </FormGroup>

                    {/* button/status */}
                    <div className="simulate-button-wrap">
                        <Button
                            bsStyle="primary"
                            className="simulate-button"
                            onClick={this._handleButtonClick}
                            disabled={canNotBeClassified || isSimulating || !enableButton}>
                            { isSimulating && <i  className="fa fa-spinner fa-spin" /> }
                            Classify
                        </Button>
                    </div>
                </div>

                {/* status && confidence */}
                { !isSimulating && (
                    <div className="simulate-info">
                    { status !== null && status !== undefined && ( // could be false
                        <div className="status-wrap">
                            <SimulateStatus status={status} />
                        </div>
                    ) }
                    { confidence !== null && confidence !== undefined && ( // could be 0
                        <div className="confidence-wrap">
                            <strong>Confidence:</strong><Progress value={confidence} />
                        </div>
                    ) }
                    </div>
                ) }


                {/* results */}
                { !isSimulating && (
                    <div className="simulate-results">

                        { isDropContent && (
                            <div className="simulate-results-bar">
                                <i
                                    className={`simulate-results-toggle ${iconClass}`}
                                    onClick={this._toggleDrop} />
                            </div>
                        ) }

                        <div className="simulate-results-list">
                            <SimulateResult
                                short={true}
                                sample={sample}/>
                            { isDropContent && isOpen && <div>{ this._renderResults(resultsPerClassifier) }</div> }
                        </div>
                    </div>
                ) }
            </div>
        )
    }
}

const mapStateToProps = (state) => {
  return {
    status: state.simulateModule.get('status'),
    confidence: state.simulateModule.get('confidence'),
    sample: state.simulateModule.get('sample'),
    resultsPerClassifier: state.simulateModule.get('resultsPerClassifier'),
    isSimulating: state.simulateModule.get('isSimulating'),
    isSimulatedFormulaDirty: state.simulateModule.get('isSimulatedFormulaDirty'),
    id: state.createExperimentModule.get('id')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    simulateOnServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(Simulate);
