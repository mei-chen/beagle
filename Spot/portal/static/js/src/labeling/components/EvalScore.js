import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Map } from 'immutable';
import { Modal, ModalHeader, ModalBody, Table } from 'react-bootstrap';
import uuidV4 from 'uuid/v4';

import {
  getScoresFromServer as getScores
} from 'labeling/redux/modules/export_dataset_module';

class EvalScore extends Component {
  constructor(props) {
    super(props);
    this._getData = this._getData.bind(this);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._renderScores = this._renderScores.bind(this);

    this.state = {
      showModal: false
    }
  }

  _showModal() {
    this.setState({ showModal: true });
    this._getData();
  }

  _hideModal() {
    this.setState({ showModal: false });
  }

  _getData() {
    const { taskId, assignmentId, getScores } = this.props;
    getScores(uuidV4(), taskId, assignmentId)
  }

  _renderScores(data) {
    return data.map((sample, i) => {
      const wright = sample.get('label') === sample.get('gold'); // skipped also are treated as wrong

      return (
        <tr
          key={i}
          className={`scr-row ${wright ? 'scr-row--wright' : 'scr-row--wrong'}`}>
          <td className="scr-text">{ sample.get('text') }</td>
          <td className="scr-gold">
            <span className={`scr-circle ${sample.get('gold') ? 'scr-circle--true' : 'scr-circle--false'}`} />
          </td>
          <td className="scr-label">
            { sample.get('label') === null ? (
              <span className="scr-skipped">Skipped</span>
            ) : (
              <span className={`scr-circle ${sample.get('label') ? 'scr-circle--true' : 'scr-circle--false'}`} />
            ) }
          </td>
          <td className="scr-status">
            { wright ? <i className="fa fa-check" /> : <i className="fa fa-ban" /> }
          </td>
        </tr>
      )
    })
  }

  render() {
    const { scores, value, max } = this.props;
    const { showModal } = this.state;

    const preparedValue = value.toFixed(1) % 1 === 0 ? +value.toFixed(0) : +value.toFixed(1);

    return (
      <div className="eval">
        <div
          className="eval-score"
          onClick={this._showModal}>
          <span className="eval-progress">
            <span
              className="eval-progress-fill"
              style={{ height: `${preparedValue / max * 100}%` }}/>
          </span>
          <span className="eval-value">{ preparedValue }</span>
          <span className="eval-max">/ { max }</span>
        </div>

        <Modal
          show={showModal}
          onHide={this._hideModal}>
          <ModalHeader closeButton>
            <h3>User result</h3>
          </ModalHeader>
          <ModalBody>
            { scores.get('isLoading') && <i className="fa fa-spinner fa-spin" /> }
            { scores.get('data').size > 0 && (
              <Table className="scr">
                <thead>
                  <tr>
                    <th className="scr-text">Sample</th>
                    <th className="scr-gold">Gold</th>
                    <th className="scr-label">Label</th>
                    <th className="scr-status">Result</th>
                  </tr>
                </thead>
                <tbody>
                  { this._renderScores(scores.get('data')) }
                </tbody>
              </Table>
            ) }
          </ModalBody>
        </Modal>
      </div>
    )
  }
};

const mapStateToProps = state => ({
  scores: state.exportDatasetModule.get('scores')
});

const mapDispatchToProps = dispatch => (
  bindActionCreators({
    getScores
  }, dispatch)
)

EvalScore.propTypes = {
  taskId: PropTypes.number.isRequired,
  assignmentId: PropTypes.number.isRequired,
  scores: PropTypes.instanceOf(Map),
  value: PropTypes.number.isRequired,
  max: PropTypes.number.isRequired
};

export default connect(mapStateToProps, mapDispatchToProps)(EvalScore);
