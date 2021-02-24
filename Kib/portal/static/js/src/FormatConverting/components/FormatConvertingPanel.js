import React from 'react';
import PropTypes from 'prop-types';
import ImmutablePropTypes from 'react-immutable-proptypes';
import { projectPropType } from 'ProjectManagement/propTypes';
import { batchPropType } from 'BatchManagement/propTypes';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid } from 'react-bootstrap';
import FormatConvertController from 'FormatConverting/components/FormatConvertController';

import { getBatchForProject } from 'base/redux/modules/batches';
import { getProjects } from 'base/redux/modules/projects';
import { getFilesForBatch } from 'base/redux/modules/files';
import { getDocForBatch } from 'base/redux/modules/documents';
import { PROJECT_NOT_SELECTED } from "base/components/ProjectSelect";
import ProjectBatchSelectForm from "base/components/ProjectBatchSelectForm";
import { all } from 'base/utils/misc';

import { MODULE_NAME } from 'FormatConverting/constants';


class FormatConvertingPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedProject: PROJECT_NOT_SELECTED,
      selectedBatch: 0,
    };
    this.selectProject = this.selectProject.bind(this);
    this.selectBatch = this.selectBatch.bind(this);
  }

  selectProject(project) {
    this.setState({
      selectedProject: project,
      selectedBatch: 0
    });
    if (project) {
      this.props.getBatchForProject(project, MODULE_NAME);
    }
  }

  selectBatch(batch) {
    this.setState({ selectedBatch: batch });
    if (batch) {
      this.props.getFilesForBatch(batch, MODULE_NAME, true);
      this.props.getDocForBatch(batch, MODULE_NAME);
    }
  }

  render() {
    const FormatConvertControllerComponent = (display) => {
      if (!display) return null;
      return (
        <div>
          <h4>Files</h4>
          <FormatConvertController batch={this.state.selectedBatch}/>
        </div>
      )
    };

    return (
      <Grid>
        <ProjectBatchSelectForm
          onProjectChange={this.selectProject}
          onBatchChange={this.selectBatch}
          batches={this.props.project_batches}
          displayAllOption={false}
        />
        {
          FormatConvertControllerComponent(all(this.state.selectedProject, this.state.selectedBatch))
        }
      </Grid>
    );
  }
}

FormatConvertingPanel.propTypes = {
  projects: ImmutablePropTypes.listOf(projectPropType).isRequired,
  project_batches: ImmutablePropTypes.listOf(batchPropType)
};

const mapStateToProps = (state) => {
  return {
    projects: state.global.projects,
    project_batches: state[ MODULE_NAME ].project_batches,
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getProjects, getBatchForProject, getFilesForBatch, getDocForBatch
  }, dispatch)
};


export default connect(mapStateToProps, mapDispatchToProps)(FormatConvertingPanel);
