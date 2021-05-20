import React from "react";
import PropTypes from "prop-types";
import { Modal, ProgressBar, ListGroup, ListGroupItem } from "react-bootstrap";

function ProgressPopup({ isOpen, onClose, title, items, total }) {
  let item_list = Object.keys(items).sort().map(function(key) {
    return {...items[key], name: key}
  });


  return (
    <Modal show={isOpen} bsSize="large" onHide={onClose}>

      <Modal.Header closeButton={items.length >= total}>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {item_list.length < total ? `Uploading ${item_list.length} of ${total}...` : `Finished: uploaded ${item_list.length} files`}
        {item_list.length < total ? <ProgressBar active now={item_list.length * 100 / total} /> : <ProgressBar now={100} />}
        <ListGroup fill>
          {item_list.map((el) => (
            <ListGroupItem bsStyle={el.error ? 'danger' : 'success'} key={el.name}>
              {el.name} {el.progress == 100 ? <ProgressBar now={100} /> : <ProgressBar active now={el.progress} />} {el.progress + '%'} {el.error ? ': ' + el.error : ''}
            </ListGroupItem>
          ))}
        </ListGroup>
      </Modal.Body>

    </Modal>
  );
}

ProgressPopup.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  items: PropTypes.array.isRequired,
  total: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
};

export default ProgressPopup;
