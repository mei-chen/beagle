import React, { PropTypes } from 'react';
import { Modal, ModalHeader, ModalBody, Button } from 'react-bootstrap';

import './styles/ConfirmDeleteModal.scss';

const ConfirmDeleteModal = ({ show, onHide, title, content, onSubmit }) => {
  return (
    <Modal
      className="confirm-delete-modal"
      show={show}
      onHide={onHide}>
      <ModalHeader>
        <h4 className="confirm-delete-modal-title">{ title }</h4>
      </ModalHeader>
      <ModalBody>
        <div className="confirm-delete-modal-content">{ content }</div>
        <div className="confirm-delete-modal-buttons">
          <Button
            className="confirm-delete-modal-button"
            bsStyle="primary"
            onClick={onSubmit}>Ok</Button>
          <Button
            className="confirm-delete-modal-button"
            onClick={onHide}>Cancel</Button>
        </div>
      </ModalBody>
    </Modal>
  )
};

ConfirmDeleteModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  content: PropTypes.string,
  onSubmit: PropTypes.func.isRequired
};

export default ConfirmDeleteModal;
