import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';
import CleanupFilesController from 'CleanupDocument/components/CleanupFilesController';
import ToolSelect from 'CleanupDocument/components/ToolSelect';
import { projectPropType } from 'ProjectManagement/propTypes';

import { getBatchForProject } from 'base/redux/modules/batches';
import { getDocForBatch } from 'base/redux/modules/documents';
import { getCleanupDocTools } from 'base/redux/modules/tools';
import { PROJECT_NOT_SELECTED, PROJECT_ALL } from "base/components/ProjectSelect";
import ProjectBatchSelectForm from "base/components/ProjectBatchSelectForm";

import { MODULE_NAME } from 'CleanupDocument/constants';

class CleanupDocumentPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedProject: PROJECT_NOT_SELECTED,
      selectedBatch: null,
      selectedTool: null
    };
    this.selectTool = (tool) => this.setState({selectedTool: tool});
    this.selectProject = this.selectProject.bind(this);
    this.selectBatch = this.selectBatch.bind(this);
  }

  selectProject(projectId) {
      this.setState({
        selectedProject: projectId,
        selectedBatch: null,
        selectedTool: null
      });
      this.props.getBatchForProject(projectId, MODULE_NAME, projectId === PROJECT_ALL);
  }

  selectBatch(batchId) {
      this.setState({selectedBatch: batchId});
      this.props.getDocForBatch(batchId, MODULE_NAME);
  }

  renderCleanupFilesController() {
    const {selectedTool, selectedBatch} = this.state;

    return (
      <div>
        <CleanupFilesController batchId={selectedBatch} tool={selectedTool} />
      </div>
    );
  }

  render() {

    return (
      <Grid>
        <ProjectBatchSelectForm
          onProjectChange={this.selectProject}
          onBatchChange={this.selectBatch}
          batches={this.props.project_batches}
        />
        <Col xs={12} md={12}>
          {
            // Show Cleanup tools list if Batch and Project is selected
            this.state.selectedProject !== null
            && this.state.selectedBatch !== null
            ? <ToolSelect /> : null
          }
          {
            this.state.selectedProject !== null
            && this.state.selectedBatch !== null
            ? this.renderCleanupFilesController() : null
          }
        </Col>
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    project_batches: state[MODULE_NAME].get('project_batches'),
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getBatchForProject, getCleanupDocTools, getDocForBatch
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(CleanupDocumentPanel);
