import React, { PropTypes } from 'react';
import { Modal, ModalHeader, ModalBody } from 'react-bootstrap';
import LabelItem from 'base/components/LabelItem';

const MappingInfoModal = ({ show, onHide }) => {
  return (
    <Modal
      className="custom-modal"
      show={show}
      onHide={onHide} >
      <ModalHeader closeButton>
        <span className="custom-modal-title">
          <i className="fa fa-question-square" />
          <span>Mapping labels to Positive/Negative</span>
        </span>
      </ModalHeader>
      <ModalBody>
        <p className="custom-modal-block">Turns multi-labeled datasets into binary decisions. The best fit for classifiers that make Yes/No predictions.</p>
        <div className="custom-modal-block clearfix">
          <div className="custom-modal-image">
            <img src="/static/img/beagle-info.svg" />
          </div>
          <span className="custom-modal-subtitle">Dogs detection dataset</span>
          <div className="label-items-list">
            <LabelItem
              isStatic
              status="pos"
              title="beagle" />
            <LabelItem
              isStatic
              status="neg"
              title="horse" />
            <LabelItem
              isStatic
              status="pos"
              title="husky" />
            <LabelItem
              isStatic
              status="neg"
              title="cat" />
            <LabelItem
              isStatic
              status="def"
              title="carrot" />
          </div>
        </div>
        <div className="tags">
          <div className="tags-group">
            <strong className="tag tag--pos">Positive:</strong> beagle, husky
          </div>
          <div className="tags-group">
            <strong className="tag tag--neg">Negative:</strong> horse, cat
          </div>
          <div className="tags-group">
            <strong className="tag tag--def">Irrelevant:</strong> carrot
          </div>
        </div>
      </ModalBody>
    </Modal>
  )
};

MappingInfoModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired
};

export default MappingInfoModal;

