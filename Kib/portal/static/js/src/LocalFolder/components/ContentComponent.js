import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import ListOfBatches from "base/components/ListOfBatches";
import ModalForm from "base/components/ModalForm";
import ProgressPopup from "base/components/ProgressPopup";
import BatchForm from "base/components/BatchForm";
import { getProjects } from 'base/redux/modules/projects';
import { getBatches } from "base/redux/modules/batches";
import { hideFilesPopup } from 'base/redux/modules/files';
import AddFileToBatchForm from "LocalFolder/components/AddFileToBatchForm";
import PickerPanel from "LocalFolder/components/PickerPanel";
import { showNotification } from "Messages/actions";
import {
  createBatch,
  createFile
} from "LocalFolder/redux/actions";
import "LocalFolder/scss/app.scss";


class ContentComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      showCreateBatchModal: false,
      showUpdateBatchModal: false,
      file: []
    };
    this.CreateBatch = this.CreateBatch.bind(this);
    this.UpdateBatch = this.UpdateBatch.bind(this);
    this.closeProgress = this.closeProgress.bind(this);
    this.onFormFieldChange = this.onFormFieldChange.bind(this);
  }

  onFormFieldChange(ev) {
    let totalFilesSize = 0;
    for (const file in ev.target.files) {
      totalFilesSize += ev.target.files[file].size || 0;
    };
    if (totalFilesSize > window.CONFIG.MAX_UPLOAD_SIZE) {
      this.props.showNotification({
        message: 'Maximum total files size is ' + (window.CONFIG.MAX_UPLOAD_SIZE / 1024 / 1024) + ' MB',
        position: 'br',
        autoDismiss: 15
      }, 'warning');
      this.setState({[ev.target.name]: []});
    } else {
      this.setState({[ev.target.name]: ev.target.files});
    }
  }

  CreateBatch(data) {
    data['project'] = data['project'] ? [data['project']] : [];
    this.props.createBatch(Object.assign({}, data, { content: this.state.file }))
      .then(this.setState({ showCreateBatchModal: false }));
  }

  UpdateBatch(data) {
    this.props.createFile(Object.assign({}, data, { content: this.state.file }))
      .then(this.setState({ showUpdateBatchModal: false }));
  }

  closeProgress() {
    this.props.hideFilesPopup();
    this.props.getBatches();
    document.getElementById("batchFile-file").value = '';
  }

  componentDidMount() {
    if (!this.props.projectStore.size) this.props.getProjects()
  }

  render() {
    const { projectStore, batchStore, fileStore, hidePopup } = this.props;
    return (
      <div className="wrapper local-wrapper">
        <PickerPanel
          onAddAsBatchClick={() => this.setState({showCreateBatchModal: true})}
          onAddToBatchClick={() => this.setState({showUpdateBatchModal: true})}
          onFormFieldChange={this.onFormFieldChange}
          isFileSelected={!!this.state.file.length}
        />

        <ListOfBatches />

        <ModalForm
          isOpen={this.state.showCreateBatchModal}
          onClose={() => this.setState({showCreateBatchModal: false})}
          title="Create New Batch"
        >
          <BatchForm
            onSubmit={data => this.CreateBatch(data)}
            projectStore={projectStore}
          />
        </ModalForm>

        <ModalForm
          isOpen={this.state.showUpdateBatchModal}
          onClose={() => this.setState({showUpdateBatchModal: false})}
          title="Add File To Batch"
        >
          <AddFileToBatchForm
            onSubmit={data => this.UpdateBatch(data)}
            batchStore={batchStore}
          />
        </ModalForm>
        <ProgressPopup
          isOpen={fileStore.popup}
          total={this.state.file.length}
          onClose={this.closeProgress}
          title="Uploading files"
          items={fileStore.list}
        />
      </div>
    )
  }
}

ContentComponent.propTypes = {
  createBatch: PropTypes.func.isRequired,
  createFile: PropTypes.func.isRequired,
  getProjects: PropTypes.func.isRequired
};


const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({
    createBatch, createFile, getProjects, hideFilesPopup, getBatches, showNotification
  }, dispatch);
};


const mapStateToProps = (state) => {
  return {
    formStore: state.formStore,
    batchStore: state.global.batches,
    projectStore: state.global.projects,
    fileStore: state.global.files
  };
};


// Use default export for the connected component (for app)
export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
