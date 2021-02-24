import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Button } from 'react-bootstrap'
import DataTable from 'base/components/DataTable';
import CreateExperimentModal from './CreateExperimentModal';

// App
import 'experiments/scss/app.scss';

import { getFromServer, deleteFromServer } from 'experiments/redux/modules/experiments_module';
import { uninviteOnServer, EXPERIMENT } from 'base/redux/modules/collaborators_module'; 

class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this._deleteExperiment = this._deleteExperiment.bind(this);
    this._revokeInvitation = this._revokeInvitation.bind(this);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this.state = {
      showModal: false
    }
  }

  _deleteExperiment(id) {
    this.props.deleteFromServer(id);
  }

  _revokeInvitation(id) {
    const { uninviteOnServer, getFromServer } = this.props;
    uninviteOnServer(EXPERIMENT, id).then(getFromServer);
  }

  _showModal() {
    this.setState({ showModal: true });
  }

  _hideModal() {
    this.setState({ showModal: false });
  }

  render() {
    const { isInitialized, experiments } = this.props;

    return (
      <div>
        <Button
          bsStyle="primary"
          onClick={this._showModal}>
          Create new
        </Button>

        <hr />

        {
          isInitialized && experiments.size > 0 ? (
            <DataTable
              type="experiments"
              data={experiments}
              onDelete={this._deleteExperiment}
              onRevoke={this._revokeInvitation} />
          ) : (
            <div className="empty-list">
              <span>No dataset</span>
            </div>
          )
        }

        <CreateExperimentModal 
          show={this.state.showModal} 
          onHide={this._hideModal} />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    isInitialized: state.experimentsModule.get('isInitialized'),
    experiments: state.experimentsModule.get('experiments')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    deleteFromServer,
    uninviteOnServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
