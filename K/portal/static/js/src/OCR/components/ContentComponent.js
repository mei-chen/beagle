import React from "react";
import axios from 'axios';
import { Grid, Col, Row, Alert } from "react-bootstrap";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import { Set } from "immutable";
import { sendPost } from "base/utils/requests";
import BatchForm from "base/components/BatchForm";
import ModalForm from "base/components/ModalForm";
import { pushMessage } from "Messages/actions";
import { PROJECT_NOT_SELECTED, PROJECT_ALL } from "base/components/ProjectSelect";
import ProjectBatchSelectForm from "base/components/ProjectBatchSelectForm";
import FileSelect from "OCR/components/FileSelect";
import ConfirmButtons from "OCR/components/ConfirmButtons";
import { setTaskState, addProcessingFiles, updateBatch, insertBatch, clearAlert } from "OCR/redux/actions";
import { getFilesForBatch } from 'base/redux/modules/files';
import { getBatchForProject } from 'base/redux/modules/batches';


const ProcessingAlert = ({ processingFiles, alert, onDismiss }) => {
  if (!alert.size) return null;
  let summary = '';
  if (processingFiles.size) {
    summary = <p>{processingFiles.size} file{processingFiles.size > 1 && 's'} sent to the JustOCR.</p>
  }
  return (
    <Row>
      <Alert bsStyle={alert.get('level', 'info')} onDismiss={onDismiss}>
        {summary}
        {alert.get('text')}
      </Alert>
    </Row>
  )
};

class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      projectId: PROJECT_NOT_SELECTED,
      batchId: 0,
      files: new Set(),
      isModalOpen: false
    };
    this.onProjectChange = this.onProjectChange.bind(this);
    this.onBatchChange = this.onBatchChange.bind(this);
    this.isFileSelected = this.isFileSelected.bind(this);
    this.updateFileIds = this.updateFileIds.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleModalSubmit = this.handleModalSubmit.bind(this);
    this.handleProcessAndReplace = this.handleProcessAndReplace.bind(this);
  }

  onProjectChange(projectId) {
    this.props.getBatchForProject(projectId, '/ocr', projectId === PROJECT_ALL);
    this.setState({ projectId: projectId, batchId: 0 });
  };

  onBatchChange(batchId) {
    this.props.getFilesForBatch(batchId, '/ocr');
    this.setState({ batchId: batchId });
  };

  isFileSelected(id) {
    return this.state.files.has(id)
  };

  updateFileIds(id) {
    const { files } = this.state;
    const insertArray = (ids) => this.setState({ files: files.merge(id) });
    const remove = (id) => this.setState({ files: files.filterNot(idInList => idInList === id) });
    const clear = () => this.setState({ files: files.clear() });
    const add = (id) => this.setState({ files: files.add(id) });
    if (!id) clear();
    else if (typeof id === 'object') insertArray(id);
    else if (this.isFileSelected(id)) remove(id);
    else add(id);
  };

  handleError(e) {
    this.props.pushMessage(e.message, 'error');
    this.props.setTaskState(false);
  }

  handleModalSubmit(data) {
    data.files = this.state.files;
    data[ 'project' ] = data[ 'add_project' ] || [];
    this.props.setTaskState(true);
    sendPost(window.CONFIG.API_URLS.ocrApiCreate, data)
      .then(() => {
        this.setState({ isModalOpen: false });
        this.props.addProcessingFiles(this.state.files);
        this.setState({ files: this.state.files.clear() })
      })
      .catch(this.handleError)
  };

  handleProcessAndReplace() {
    const data = { files: this.state.files };
    this.props.setTaskState(true);
    sendPost(window.CONFIG.API_URLS.ocrApiReplace, data)
      .then(() => {
        this.props.addProcessingFiles(this.state.files);
        this.setState({ files: this.state.files.clear() })
      })
      .catch(this.handleError);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.reloadBatchRules.get('need')) {
      const type = nextProps.reloadBatchRules.get('type');
      axios.get(nextProps.reloadBatchRules.get('from'))
        .then(({ data }) => {
          if (type === 'update') this.props.updateBatch(data);
          if (type === 'create') this.props.insertBatch(data);
        })
        .catch(e => this.props.pushMessage(e.response, 'error'));
    }
  }

  render() {
    const { processingFiles, alert, clearAlert } = this.props;
    return (
      <Grid>
        <ProcessingAlert
          processingFiles={processingFiles}
          alert={alert}
          onDismiss={clearAlert}
        />
        <ProjectBatchSelectForm
          onProjectChange={this.onProjectChange}
          onBatchChange={this.onBatchChange}
          batches={this.props.batches}
        />
        {
          !!this.state.batchId &&
          <div>
            <Row>
              <FileSelect
                batchId={this.state.batchId}
                updateFileIds={this.updateFileIds}
                files={this.state.files}
                isFileSelected={this.isFileSelected}
              />
            </Row>

            <Row>
              <Col xs={6} md={6}>
                <ConfirmButtons
                  onSaveAsBatchClick={() => this.setState({isModalOpen: true})}
                  handleProcessAndReplace={this.handleProcessAndReplace}
                  isDisabled={!this.state.files.size}
                />
              </Col>
            </Row>

            <ModalForm
              onClose={() => this.setState({isModalOpen: false})}
              isOpen={this.state.isModalOpen}
              title="Save converted PDFs as new batch"
            >
              <BatchForm
                projectStore={this.props.projectStore}
                onSubmit={this.handleModalSubmit}
              />
            </ModalForm>
          </div>
        }
      </Grid>
    );
  }
}

export default connect(
  (state) => ({
    projectStore: state.global.projects,
    batches: state.ocrStore.get('batches'),
    reloadBatchRules: state.ocrStore.get('reloadBatchRules'),
    processingFiles: state.ocrStore.get('processingFiles'),
    alert: state.ocrStore.get('alert')
  }),
  (dispatch) => bindActionCreators({
    pushMessage,
    getFilesForBatch,
    getBatchForProject,
    setTaskState,
    addProcessingFiles,
    insertBatch,
    updateBatch,
    clearAlert
  }, dispatch)
)(ContentComponent);
