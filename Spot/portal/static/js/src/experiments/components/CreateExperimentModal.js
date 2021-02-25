import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { toJS } from 'immutable';
import { Modal, Form, FormGroup, FormControl, Button, Alert } from 'react-bootstrap';
import { postToServer, resetPostError, getDefNameFromServer, defaultFormula } from 'experiments/redux/modules/experiments_module';

class CreateExperimentModal extends Component {
  constructor(props) {
    super(props);
    this._handleFormSubmit = this._handleFormSubmit.bind(this);
    this._handleInputChange = this._handleInputChange.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._suggestName = this._suggestName.bind(this);
    this.state = {
      name: props.defaultName
    }
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.defaultName !== nextProps.defaultName) this.setState({ name: nextProps.defaultName })
  }

  _handleFormSubmit(e) {
    e.preventDefault();
    this.props.postToServer({
      name: this.state.name,
      formula: defaultFormula
    });
  }

  _handleInputChange(e) {
    this.setState({ name: e.target.value });
  }

  _hideModal() {
    const { defaultName, resetPostError, onHide } = this.props;
    this.setState({ name: defaultName });
    resetPostError();
    onHide();
  }

  _suggestName() {
    this.props.getDefNameFromServer();
  }

  render() {
    const { show, errorMessage } = this.props;
    const { name } = this.state;

    return (
      <Modal
        show={show}
        onHide={this._hideModal}
        onEnter={this._suggestName}>
        <Modal.Header closeButton>
          <Modal.Title>Create Experiment</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form
            onSubmit={this._handleFormSubmit}>
            <FormGroup>
              <FormControl
                type="text"
                value={name}
                onChange={this._handleInputChange} />
            </FormGroup>
            { !!errorMessage && <Alert bsStyle="danger">{ errorMessage }</Alert> }
            <Button
              type="submit"
              bsStyle="success"
              disabled={!name}>
              Create
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
    )
  }
}

CreateExperimentModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired,
  defaultName: PropTypes.string.isRequired,
  postToServer: PropTypes.func.isRequired,
  getDefNameFromServer: PropTypes.func.isRequired,
  resetPostError: PropTypes.func.isRequired,
  errorMessage: PropTypes.string.isRequired
}

const mapStateToProps = state => ({
  errorMessage: state.experimentsModule.get('postErrorMessage'),
  defaultName: state.experimentsModule.get('defaultName')
});

const mapDispatchToProps = dispatch => bindActionCreators({
  postToServer,
  getDefNameFromServer,
  resetPostError
}, dispatch)

export default connect(mapStateToProps, mapDispatchToProps)(CreateExperimentModal);
