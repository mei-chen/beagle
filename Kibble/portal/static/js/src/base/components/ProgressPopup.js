import React from "react";
import PropTypes from "prop-types";
import { Modal, ProgressBar, ListGroup, ListGroupItem } from "react-bootstrap";

const ProgressPopup = ({ isOpen, onClose, title, items,
                          total}) => (
  <Modal show={isOpen} bsSize="large" onHide={onClose}>

    <Modal.Header closeButton={items.length >= total}>
      <Modal.Title>{title}</Modal.Title>
    </Modal.Header>

    <Modal.Body>
      {items.length < total ? `Uploading ${items.length} of ${total}...` : `Finished: uploaded ${items.length} files`}
      {items.length < total ? <ProgressBar active now={items.length * 100 / total} /> :  <ProgressBar  now={100} /> }
      <ListGroup fill>
        {items.reverse().map((el) => (
          <ListGroupItem bsStyle={el.error ? 'danger' : 'success'} key={el.name}>
            {el.name} {el.error ? ': ' + el.error : ''}
          </ListGroupItem>
        ))}
      </ListGroup>
    </Modal.Body>

  </Modal>
);

ProgressPopup.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  items: PropTypes.array.isRequired,
  total: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
};

export default ProgressPopup;
