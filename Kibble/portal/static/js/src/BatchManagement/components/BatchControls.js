import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import ImmutablePropTypes from 'react-immutable-proptypes';
import { Button, ButtonToolbar, Glyphicon, Panel, Grid, Col } from 'react-bootstrap';
import { batchPropType } from "BatchManagement/propTypes";
import { MODULE_NAME } from "BatchManagement/constants";
import UserManagementModal from "BatchManagement/components/UserManagementModal"
import { showForm, closeForm, showUserManagement, closeUserManagement } from "BatchManagement/redux/actions";
import { patchBatch, getBatches, deleteBatch } from "base/redux/modules/batches";
import { pushMessage } from "Messages/actions";
import { DefaultButtons } from "base/components/FormControls";
import BatchForm from 'base/components/BatchForm';
import ModalForm from 'base/components/ModalForm';

class BatchControls extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedBatch: null
    };
    this.onEdit = () => this.props.showForm();
    this.onSubmit = this.onSubmit.bind(this);
    this.onRemove = this.onRemove.bind(this);
    this.selectBatch = (batch) => this.setState({ selectedBatch: batch });
  }

  componentDidMount() {
    const { batches } = this.props;
    if(!batches.size) this.props.getBatches();
  }

  componentWillReceiveProps(nextProps) {
    const { batches, selectedBatchId } = nextProps;

    if(batches.size && selectedBatchId) {
      this.setState({
        selectedBatch: batches.find(batch => batch.id === selectedBatchId)
      })
    }
  }

  onSubmit(data) {
    const { patchBatch, closeForm } = this.props;
    patchBatch(
      this.state.selectedBatch.resource_uri,
      { name: data.name, description: data.description, project: data.project },
      closeForm,
      e => pushMessage(e, 'error'),
      (data) => {
        this.selectBatch(data);
        return getBatches()
      }
    );
  }

  onRemove(id) {
    const { selectedBatch } = this.state;
    const { deleteBatch, getBatches } = this.props;

    deleteBatch(selectedBatch.id)
      .then(_ => getBatches());
  }

  render() {
    const { showUserManagement } = this.props;
    return (
      <div>
        <Panel>
          <ButtonToolbar>
            <Button bsSize="small" onClick={this.onEdit}
                    disabled={!this.state.selectedBatch}>
              Edit Batch Details <i className="fal fa-edit"></i>
            </Button>
            <Button bsSize="small" onClick={showUserManagement}
                    disabled={!this.state.selectedBatch}>
              Manage Collaborators <i className="fal fa-users"></i>
            </Button>
            <Button bsSize="small" bsStyle="danger" onClick={this.onRemove}
                    disabled={!this.state.selectedBatch}>
              Delete Batch <i className="fal fa-trash"></i>
            </Button>
          </ButtonToolbar>
        </Panel>

        <ModalForm
          isOpen={this.props.isFormModalOpen}
          onClose={this.props.closeForm}
          title="Edit batch"
        >
          <BatchForm
            initialValues={this.state.selectedBatch}
            onSubmit={this.onSubmit}
            projectAction=""
          />
        </ModalForm>

        <ModalForm
          isOpen={this.props.isUserManagementModalOpen}
          onClose={this.props.closeUserManagement}
          title="User Management"
        >
          <UserManagementModal id={this.state.selectedBatch && this.state.selectedBatch.id}/>
        </ModalForm>
      </div>
    );
  }
}


BatchControls.propTypes = {
  batches: ImmutablePropTypes.listOf(batchPropType).isRequired,
  selectedBatchId: PropTypes.number // could be null
};

const mapStateToProps = (state) => {
  return {
    batches: state.global.batches,
    isFormModalOpen: state[ MODULE_NAME ].get('isFormModalOpen'),
    isUserManagementModalOpen: state[MODULE_NAME].get('isUserManagementModalOpen')
  };
};

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({
    showForm, closeForm, patchBatch, getBatches, deleteBatch, closeUserManagement, showUserManagement
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(BatchControls);
