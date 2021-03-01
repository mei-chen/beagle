import React from 'react';
import PropTypes from 'prop-types';
import { List } from 'immutable';
import { ListGroup, ListGroupItem, Grid, Col } from 'react-bootstrap';
import CleanupSentencesController from './CleanupSentencesController';
import ProjectBatchSelectForm from 'base/components/ProjectBatchSelectForm';


class ProjectListItem extends React.Component {
  constructor(props) {
    super(props);
    const { project, handleSelect } = this.props;
    this.select = () => handleSelect(project);
  }

  render() {
    const { project, active } = this.props;
    return (
      <ListGroupItem
        active={active}
        onClick={this.select}>
        Project {project}
      </ListGroupItem>
    );
  }
}

ProjectListItem.propTypes = {
  active: PropTypes.bool,
  handleSelect: PropTypes.func,
  project: PropTypes.number,
};

class BatchListItem extends React.Component {
  constructor(props) {
    super(props);
    const { batch, handleSelect } = this.props;
    this.select = () => handleSelect(batch);
  }

  render() {
    const { batch, active } = this.props;
    return (
      <ListGroupItem
        active={active}
        onClick={this.select}>
        Batch {batch}
      </ListGroupItem>
    );
  }
}

BatchListItem.propTypes = {
  active: PropTypes.bool,
  handleSelect: PropTypes.func,
  batch: PropTypes.number,
};

class CleanupToolsListItem extends React.Component {
  constructor(props) {
    super(props);
    const { tool, handleSelect } = this.props;
    this.select = () => handleSelect(tool);
  }

  render() {
    const { tool, active } = this.props;
    return (
      <ListGroupItem
        active={active}
        onClick={this.select}>
        {tool}
      </ListGroupItem>
    );
  }
}

CleanupToolsListItem.propTypes = {
  active: PropTypes.bool,
  handleSelect: PropTypes.func,
  tool: PropTypes.number,
};

class CleanupSentencesPanel extends React.Component { // eslint-disable-line react/no-multi-comp
  constructor(props) {
    super(props);
    this.state = {
      selectedProject: null,
      selectedBatch: null,
      selectedTool: null,
    };

    this.selectProject = project => this.setState({selectedProject: project});
    this.selectBatch = batch => this.setState({selectedBatch: batch});
    this.selectTool = tool => this.setState({selectedTool: tool});
  }

  renderListOfProjects() {
    const { selectedProject } = this.state;
    return [1, 2, 3, 4, 5, 6, 7, 8, 9].map((v, k) => (
      <ProjectListItem
        key={k}
        project={v}
        active={v === selectedProject}
        handleSelect={this.selectProject}
        />
    ));
  }

  renderListOfBatches() {
    const { selectedBatch } = this.state;
    return [1, 2, 3, 4, 5, 6, 7, 8, 9].map((v, k) => (
      <BatchListItem
        key={k}
        batch={v}
        active={v === selectedBatch}
        handleSelect={this.selectBatch}
        />
    ));
  }

  renderToolList() {
    const { selectedTool } = this.state;
    return [
        'Listing numbers',
        'Spelling check'
    ].map((v, k) => (
      <CleanupToolsListItem
        key={k}
        tool={v}
        active={v === selectedTool}
        handleSelect={this.selectTool}
        />
    ));
  }

  render() {
    const listgroupProjects = (
        <div>
          <h4>Project</h4>
          <div className="project-list-selector">
            <Grid>
              <Col xs={12} md={12}>
                <ListGroup>
                  {this.renderListOfProjects()}
                </ListGroup>
              </Col>
            </Grid>
          </div>
         </div>
    );

    const listgroupBatches = (
        <div>
          <h4>Batch</h4>
          <div className="project-list-selector">
          <Grid>
            <Col xs={12} md={12}>
              <ListGroup>
                {this.renderListOfBatches()}
              </ListGroup>
              </Col>
            </Grid>
          </div>
        </div>
    );

    const cleanupSentences = (
        <div>
          <h4>Cleanup Tools</h4>
          <div className="project-list-selector">
          <Grid>
            <Col xs={12} md={12}>
              <ListGroup>
                {this.renderToolList()}
              </ListGroup>
              </Col>
            </Grid>
          </div>
        </div>
    );

    const CleanupSentencesComponent = (
        <div>
          <CleanupSentencesController />
        </div>
    );

    const batches = List([{id: 1, name: 'foo'}, {id: 2, name: 'bar'}]);

    return (
      <Grid>
        <Col xs={12} md={12}>
        <ProjectBatchSelectForm
          onProjectChange={(id) => this.setState({ selectedProject: id })}
          batches={batches}
          onBatchChange={(id) => this.setState({ selectedBatch: id })}
        />
        {
          // Show Cleanup tools list if Batch and Project is selected
          this.state.selectedProject !== null
          && Number.isInteger(this.state.selectedProject)
          && this.state.selectedBatch !== null
          && Number.isInteger(this.state.selectedBatch)
          ? cleanupSentences : null
        }
        {
          this.state.selectedTool !== null
          ? CleanupSentencesComponent : null
        }
        </Col>
      </Grid>
    );
  }
};

CleanupSentencesPanel.defaultProps = {
};

export default CleanupSentencesPanel;
