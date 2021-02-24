import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid } from 'react-bootstrap';

import BatchControls from 'BatchManagement/components/BatchControls';
import FileController from 'BatchManagement/components/FileController';
import { getFilesForBatch, getFreeFiles } from 'BatchManagement/redux/actions';
import { getBatchForProject } from 'base/redux/modules/batches';
import { getProjects } from 'base/redux/modules/projects';
import { batchPropType } from 'ProjectManagement/propTypes';
import { projectPropType } from 'ProjectManagement/propTypes';
import { MODULE_NAME } from 'BatchManagement/constants';
import { PROJECT_NOT_SELECTED, PROJECT_ALL } from 'base/components/ProjectSelect';
import ProjectBatchSelectForm from 'base/components/ProjectBatchSelectForm';
import { all } from 'base/utils/misc';


class BatchManagementPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedProject: PROJECT_NOT_SELECTED,
      selectedBatch: null
    };
    this.selectProject = this.selectProject.bind(this);
    this.selectBatch = this.selectBatch.bind(this);
  }

  selectProject(projectId) {
    this.setState({
      selectedProject: projectId,
      selectedBatch: null
    });
    this.props.getBatchForProject(
      projectId, '/ProjectManagement', projectId === PROJECT_ALL
    );
  }

  selectBatch(batchId) {
    this.setState({ selectedBatch: batchId });
    this.props.getFilesForBatch(batchId);
    this.props.getFreeFiles();
  }

  render() {
    return (
      <Grid>
        <ProjectBatchSelectForm
          onProjectChange={this.selectProject}
          onBatchChange={this.selectBatch}
          batches={this.props.batches}
          projectTitle="Select project to manage files"
          batchTitle="Select batch to manage files"
        />
        {
          all(this.state.selectedProject > -1, this.state.selectedBatch) &&
          <FileController batch={this.state.selectedBatch}/>
        }
        <BatchControls selectedBatchId={this.state.selectedBatch} />
      </Grid>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    batches: state[ MODULE_NAME ].get('batches')
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getProjects, getBatchForProject, getFilesForBatch, getFreeFiles
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(BatchManagementPanel);
