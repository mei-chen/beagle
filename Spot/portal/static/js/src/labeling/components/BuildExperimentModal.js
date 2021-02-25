import React, { PropTypes } from 'react';
import { Map } from 'immutable';
import { Link } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Modal, ModalHeader, ModalBody, Alert } from 'react-bootstrap';

const BuildExperimentModal = ({ show, onHide, buildingExperiment }) => {
  return (
    <Modal
      show={show}
      onHide={onHide}>
      <ModalHeader closeButton>
        <h4>Build Experiment</h4>
      </ModalHeader>
      <ModalBody>
        {/* loading */}
        { buildingExperiment.get('isLoading') && <span><i className="fa fa-spinner fa-spin fa-fw" /> Building experiment and dataset</span> }

        {/* success */}
        { buildingExperiment.get('isSuccess') && (
          <Alert bsStyle="success" className="build-experiment-alert">
            Experiment and dataset built successfully
            <ul className="saved-dataset-list">
              <li>
                <Link
                  className="saved-dataset-link"
                  to={`/datasets/${buildingExperiment.get('data').get('dataset').get('id')}/page/1`}>
                  <i className="fa fa-database" />
                  <span>{ buildingExperiment.get('data').get('dataset').get('name') }</span>
                </Link>
              </li>
              <li>
                <Link
                  className="saved-dataset-link"
                  to={`/experiments/${buildingExperiment.get('data').get('experiment').get('id')}/edit`}>
                  <i className="fa fa-lightbulb" />
                  <span>{ buildingExperiment.get('data').get('experiment').get('name') }</span>
                </Link>
              </li>
            </ul>
          </Alert>
        ) }
      </ModalBody>
    </Modal>
  )
};

BuildExperimentModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired,
  buildingExperiment: PropTypes.instanceOf(Map).isRequired
};

const mapStateToProps = state => ({
  buildingExperiment: state.labelingModule.get('buildingExperiment')
});

export default connect(mapStateToProps)(BuildExperimentModal);
