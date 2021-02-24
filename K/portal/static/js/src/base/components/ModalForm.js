import React from "react";
import PropTypes from "prop-types";
import { Modal, Button } from "react-bootstrap";

const ModalForm = ({ isOpen, onClose, title, children }) => (
  <Modal show={isOpen} bsSize="sm" onHide={onClose}>

    <Modal.Header closeButton>
      <Modal.Title>{title}</Modal.Title>
    </Modal.Header>

    <Modal.Body>{children}</Modal.Body>

    <Modal.Footer/>
  </Modal>
);

ModalForm.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired
};

export default ModalForm;
