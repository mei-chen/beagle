import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from "redux";
import axios from 'axios';
import { List } from 'immutable';
import {
  Grid, Col, Button, Panel, Glyphicon
} from 'react-bootstrap';
import { PROJECT_NOT_SELECTED, PROJECT_ALL } from "base/components/ProjectSelect";
import ProjectBatchSelectForm from "base/components/ProjectBatchSelectForm";
import { getBatchForProject } from 'base/redux/modules/batches';
import { getDocForBatch } from 'base/redux/modules/documents';
import { sendPost } from 'base/utils/requests';
import { pushMessage } from 'Messages/actions';
import { MODULE_NAME } from 'SentenceSplitting/redux/constants';
import DocumentSelect from 'SentenceSplitting/components/DocumentSelect';
import {
  populateLockedDocuments,
  clearWsMessage,
  bulkDownloadTaskSetState,
  clearBulkDownloadUrl
} from 'SentenceSplitting/redux/actions';


class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      projectId: PROJECT_NOT_SELECTED,
      batchId: 0,
      documents: new List()
    };

    this.onProjectChange = this.onProjectChange.bind(this);
    this.onBatchChange = this.onBatchChange.bind(this);
    this.isDocumentSelected = this.isDocumentSelected.bind(this);
    this.handleConvertClick = this.handleConvertClick.bind(this);
    this.handleBulkDownload = this.handleBulkDownload.bind(this);
    this.handleBulkDownloadJSON = this.handleBulkDownloadJSON.bind(this);
    this.updateDocumentIds = this.updateDocumentIds.bind(this);
  }

  onProjectChange(projectId) {
    this.props.getBatchForProject(projectId, '/SS', projectId === PROJECT_ALL);
    this.setState({ projectId, batchId: 0 })
  }

  onBatchChange(batchId) {
    this.props.getDocForBatch(batchId, '/SS');
    this.setState({ batchId })
  }

  isDocumentSelected(id) {
    return this.state.documents.indexOf(id) !== -1
  }

  handleConvertClick() {
    const data = { documents: this.state.documents };
    const endpoint = window.CONFIG.API_URLS.sentenceSplittingApi;
    sendPost(endpoint, data)
      .then(() => {
        this.props.populateLockedDocuments(this.state.documents);
        this.setState({ documents: this.state.documents.clear() })
      })
  }

  handleBulkDownload() {
    this.props.bulkDownloadTaskSetState(true);
    axios.get(`${window.CONFIG.API_URLS.downloadSentences}?batch=${this.state.batchId}`)
      .catch(() => this.props.bulkDownloadTaskSetState(false))
  }

  handleBulkDownloadJSON() {
    this.props.bulkDownloadTaskSetState(true);
    axios.get(`${window.CONFIG.API_URLS.downloadSentences}?batch=${this.state.batchId}&json=1`)
      .catch(() => this.props.bulkDownloadTaskSetState(false))
  }

  updateDocumentIds(id) {
    const { documents: doc } = this.state;
    const insertArray = (ids) => this.setState({ documents: this.state.documents.concat(ids) });
    const remove = (id) => this.setState({ documents: doc.filter(idInList => idInList !== id) });
    const clear = () => this.setState({ documents: doc.clear() });
    const add = (id) => this.setState({ documents: doc.push(id) });

    if (!id) clear();
    else if (List.isList(id)) insertArray(id);
    else if (this.isDocumentSelected(id)) remove(id);
    else add(id);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.wsMessage) {
      this.props.pushMessage(nextProps.wsMessage, 'info');
      this.props.clearWsMessage();
    }
    if (nextProps.bulkDownloadUrl) {
      window.open(nextProps.bulkDownloadUrl, '_blank');
      this.props.clearBulkDownloadUrl();
    }
  }

  render() {
    const { batchId, documents } = this.state;
    const { batches, bulkDownloadTaskState } = this.props;
    return (
      <div>
        <Grid>
          <ProjectBatchSelectForm
            onProjectChange={this.onProjectChange}
            onBatchChange={this.onBatchChange}
            batches={batches}
          />
            {
              !!batchId &&
              <div>
                <h4>Documents</h4>
                <Grid>
                    <DocumentSelect
                      batchId={batchId}
                      updateDocumentIds={this.updateDocumentIds}
                      documents={documents}
                      isDocumentSelected={this.isDocumentSelected}
                    />
                    <Col xs={12} md={12}>
                      <Panel>
                        <Button
                          onClick={this.handleConvertClick}
                          disabled={!documents.size}
                        >
                          Split sentences
                        </Button>
                        <div className="pull-right">
                          <Button onClick={this.handleBulkDownload}
                                  disabled={bulkDownloadTaskState}>
                            <Glyphicon glyph='download-alt'/>
                            {
                              bulkDownloadTaskState ? ' Please wait' : ' All CSV'
                            }
                          </Button>
                          <Button onClick={this.handleBulkDownloadJSON}
                                  disabled={bulkDownloadTaskState}>
                            <Glyphicon glyph='download-alt'/>
                            {
                              bulkDownloadTaskState ? ' Please wait' : ' All JSON'
                            }
                          </Button>
                        </div>
                      </Panel>
                    </Col>
                </Grid>
              </div>
            }
        </Grid>
      </div>
    );
  }
}

export default connect(
  (state) => ({
    projectStore: state.global.projects,
    batches: state[ MODULE_NAME ].get('batches'),
    wsMessage: state[ MODULE_NAME ].get('wsMessage'),
    bulkDownloadTaskState: state[ MODULE_NAME ].get('bulkDownloadTaskState'),
    bulkDownloadUrl: state[ MODULE_NAME ].get('bulkDownloadUrl')
  }),
  (dispatch) => bindActionCreators({
    getBatchForProject,
    getDocForBatch,
    populateLockedDocuments,
    pushMessage,
    clearWsMessage,
    bulkDownloadTaskSetState,
    clearBulkDownloadUrl
  }, dispatch)
)(ContentComponent);
