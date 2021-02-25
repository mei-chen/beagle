import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';
import { Modal, ModalHeader, ModalBody } from 'react-bootstrap';
import Truncate from 'base/components/Truncate';

class DatasetLabels extends Component {
  constructor(props) {
    super(props);
    this._hideModal = this._hideModal.bind(this);
    this._showModal = this._showModal.bind(this);
    this._renderLabels = this._renderLabels.bind(this);
    this.state = {
      showModal: false
    }
  }

  _hideModal() {
    this.setState({ showModal: false })
  }

  _showModal() {
    this.setState({ showModal: true })
  }

  _renderLabels(labels, truncateLength) {
    const { saplesPerLabel } = this.props;
    const emptyLabel = <i className="fa fa-circle" title="Empty label" />;
    return labels.map((label, i) => (
      <span
        key={i}
        className="klass-label label label-default">
        { !label ? emptyLabel : ( // could be null in old datasets
          truncateLength ? <Truncate maxLength={truncateLength}>{label}</Truncate> : label
        ) }
        { !!saplesPerLabel && <span className="klass-label-count">({ saplesPerLabel[label] })</span> }
      </span>
    ));
  }

  render() {
    const { labels, show, modal } = this.props;
    const { showModal } = this.state;

    return (
      <div className="klass-labels">
        { this._renderLabels( labels.slice(0, show ), 30 ) }

        { labels.length > show && !modal && <span>...</span> }

        { labels.length > show && modal && (
          <i
            className="klass-more fa fa-chevron-circle-right"
            title="Show all"
            onClick={this._showModal} />
        ) }

        { labels.length > show && modal && (
          <Modal
            show={showModal}
            onHide={this._hideModal}
            className="add-dataset-modal">

            <ModalHeader closeButton>
              <h2>Dataset labels</h2>
            </ModalHeader>

            <ModalBody>
              <div className="klass-list">
                { this._renderLabels(labels) }
              </div>
            </ModalBody>
          </Modal>
        ) }
      </div>
    )
  }
}

DatasetLabels.propTypes = {
  labels: PropTypes.array.isRequired,
  show: PropTypes.number,
  modal: PropTypes.bool,
  saplesPerLabel: PropTypes.object
}

DatasetLabels.defaultProps = {
  show: 3
}

export default DatasetLabels;
