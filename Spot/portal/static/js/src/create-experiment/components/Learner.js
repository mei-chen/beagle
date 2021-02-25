import React, { Component, PropTypes } from 'react';
import { Map } from 'immutable';
import { Button, Modal, ModalHeader, ModalBody } from 'react-bootstrap';
import Truncate from 'base/components/Truncate';
import SamplesTable from 'create-experiment/components/SamplesTable';
import CollectForm from 'create-experiment/components/CollectForm';

class Learner extends Component {
  constructor(props) {
    super(props);
    this._toggleDrop = this._toggleDrop.bind(this);
    this._showDataModal = this._showDataModal.bind(this);
    this._hideDataModal = this._hideDataModal.bind(this);
    this._showCollectModal = this._showCollectModal.bind(this);
    this._hideCollectModal = this._hideCollectModal.bind(this);
    this.state = {
      isOpen: false,
      showDataModal: false,
      showCollectModal: false
    }
  }

  _toggleDrop() {
    this.setState({ isOpen: !this.state.isOpen });
  }

  _showDataModal() {
    this.setState({ showDataModal: true });
  }

  _hideDataModal() {
    this.setState({ showDataModal: false });
  }

  _showCollectModal() {
    this.setState({ showCollectModal: true });
  }

  _hideCollectModal() {
    this.setState({ showCollectModal: false });
  }

  render() {
    const { learner } = this.props;
    const { isOpen, showDataModal, showCollectModal } = this.state;

    return (
      <div className="learner">
        <div className="learner-right">
          <i
            className="learner-button fa fa-cog"
            onClick={this._toggleDrop} />
        </div>

        <div className="learner-body">
          <i className="learner-icon fa fa-cube" />
          <span className="learner-title">Online learner</span>
          { learner.get('username') && (
            <span className="learner-user">
              <i className="fa fa-user" />
              <Truncate maxLength={20}>{ learner.get('username') }</Truncate>
            </span>
          ) }
          <div className="learner-samples">
            <span className="learner-samples-total">{ learner.get('stats').get('total') } samples</span>
            <span className="learner-samples-stats">
              <span className="learner-samples-pos">
                <i className="fa fa-check-circle" />
                { learner.get('stats').get('positive') },
              </span>
              <span className="learner-samples-neg">
                <i className="fa fa-minus-circle" />
                { learner.get('stats').get('negative') }
              </span>
            </span>
          </div>
        </div>

        { isOpen && (
          <div className="learner-drop">
            <Button
              className="learner-drop-button"
              onClick={this._showDataModal}>
              Show data
            </Button>

            <Button
              className="learner-drop-button"
              onClick={this._showCollectModal}>
              Collect to Dataset
            </Button>

            <Modal show={showDataModal} onHide={this._hideDataModal} className="online-db-modal" enforceFocus={false}>
              <ModalHeader closeButton><h3>Online dataset</h3></ModalHeader>
              <ModalBody>
                <SamplesTable tag={learner.get('username')} />
              </ModalBody>
            </Modal>

            <Modal show={showCollectModal} onHide={this._hideCollectModal} enforceFocus={false}>
              <ModalHeader closeButton><h3>Collect to Dataset</h3></ModalHeader>
              <ModalBody>
                <CollectForm tag={learner.get('username')} />
              </ModalBody>
            </Modal>
          </div>
        ) }
      </div>
    )
  }
}

Learner.propTypes = {
  learner: PropTypes.instanceOf(Map).isRequired
}

export default Learner;
