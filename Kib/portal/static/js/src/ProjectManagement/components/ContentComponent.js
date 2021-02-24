import React from 'react';
import PropTypes from 'prop-types';
import ImmutablePropTypes from 'react-immutable-proptypes'
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { ButtonToolbar, Button } from 'react-bootstrap';
import {
  postProjects,
  getProjects,
  patchProject,
  removeProject,
  archiveProject
} from 'base/redux/modules/projects';
import ModalForm from 'base/components/ModalForm';
import { projectPropType } from 'ProjectManagement/propTypes';
import ProjectPanel from 'ProjectManagement/components/ProjectPanel';
import ProjectsList from 'ProjectManagement/components/ProjectsList';
import ProjectManagementPanel from 'ProjectManagement/components/ProjectManagementPanel';
import UserManagementModal from "ProjectManagement/components/UserManagementModal"
import { MODULE_NAME } from 'ProjectManagement/constants';
import ProjectForm from 'ProjectManagement/components/forms';
import {
  projectCreate,
  selectProject,
  deselectProject,
  setModalOpen,
  setShowInactive,
  getInactiveProject,
  addToInactiveProject,
  getBatchForProject,
  getFreeBatches,
} from 'ProjectManagement/redux/actions';
import { getFirst } from 'base/utils/misc';


class ContentComponent extends React.Component {
  constructor(props) {
    super(props);

    this.editProject = this.editProject.bind(this);
    this.archiveProject = this.archiveProject.bind(this);
    this.getProjects = this.getProjects.bind(this);
    this.selectProject = this.selectProject.bind(this);

    this.deselectProject = () => this.props.deselectProject();
  }

  editProject(data) {
    const { patchProject, selectedProject, setModalOpen, deselectProject } = this.props;
    return patchProject(data, selectedProject.get('id'),
      [ () => setModalOpen('edit', false), deselectProject ]
    );
  }

  archiveProject() {
    const { archiveProject, selectedProject, setModalOpen, deselectProject } = this.props;
    archiveProject(
      selectedProject.get('id'),
      [() => setModalOpen('archive', false), deselectProject ]);
  }

  getProjects() {
    if (this.props.isShowInactive) {
      return this.props.inactiveProjects
    } else {
      return this.props.projects
    }
  }

  selectProject(project) {
    this.props.selectProject(project);
    this.props.getBatchForProject(project.id);
    this.props.getFreeBatches(project.id);
  }

  componentWillMount() {
    const { projects, inactiveProjects, getProjects, getInactiveProject } = this.props;
    if (!projects.size) getProjects();
    if (!inactiveProjects.size) getProjects({ status: 2 }, getInactiveProject)
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.transferToInactive) {
      for (const id of nextProps.transferToInactive) {
        // Add to the local (subapp) tree
        const archived = getFirst(this.props.projects, (obj) => obj.id === id);
        archived.status_verbose = 'Archived';
        this.props.addToInactiveProject(archived);
        // Remove from global tree
        this.props.removeProject(id);
      }
    }
  }

  render() {
    const {
      isModalOpen, setModalOpen, postProjects, selectedProject,
      isShowInactive, setShowInactive, inactiveProjects, projects
    } = this.props;
    return (
      <div className="wrapper projects-wrapper">

        <ProjectPanel
          setModalOpen={setModalOpen}
          selectedProject={selectedProject}
          setShowInactive={setShowInactive}
          isShowInactive={isShowInactive}
        />

        <ProjectsList
          projects={isShowInactive ? inactiveProjects : projects}
          selectedProject={selectedProject}
          selectProject={this.selectProject}
          deselectProject={this.deselectProject}
          isShowInactive={isShowInactive}
        />

        <ProjectManagementPanel />

        <ModalForm
          isOpen={isModalOpen.get('create')}
          onClose={() => setModalOpen('create', false)}
          title="Create new project"
        >
          <ProjectForm
            onSubmit={data => postProjects(data, () => setModalOpen('create', false))}
          />
        </ModalForm>

         <ModalForm
          isOpen={isModalOpen.get('collaborators')}
          onClose={() => setModalOpen('collaborators', false)}
          title="User Management"
        >
          <UserManagementModal id={selectedProject && selectedProject.get('id')}/>
        </ModalForm>

        <ModalForm
          isOpen={isModalOpen.get('edit')}
          onClose={() => setModalOpen('edit', false)}
          title={`Edit Project ${selectedProject.get('name')}`}
        >
          <ProjectForm
            onSubmit={this.editProject}
          />
        </ModalForm>

        <ModalForm
          isOpen={isModalOpen.get('archive')}
          onClose={() => setModalOpen('archive', false)}
          title="Are You Sure?"
        >
          <div className="text-center">
            <p>
              <strong>Do you want archive `{selectedProject.get('name')}`?</strong>
            </p>
            <ButtonToolbar style={{display: 'inline-block'}}>
              <Button
                bsStyle="danger"
                onClick={this.archiveProject}
              >
                Yes
              </Button>
              <Button onClick={() => setModalOpen('archive', false)}>No</Button>
            </ButtonToolbar>
          </div>
        </ModalForm>

      </div>
    );
  }
}


ContentComponent.propTypes = {
  projects: ImmutablePropTypes.listOf(projectPropType)
};

const mapDispatchToProps = dispatch => bindActionCreators({
  postProjects,
  getProjects,
  patchProject,
  selectProject,
  deselectProject,
  setModalOpen,
  archiveProject,
  setShowInactive,
  getInactiveProject,
  removeProject,
  addToInactiveProject,
  getBatchForProject,
  getFreeBatches
}, dispatch);

const mapStateToProps = state => ({
  projects: state.global.projects,
  inactiveProjects: state[ MODULE_NAME ].get('inactiveProjects'),
  selectedProject: state[ MODULE_NAME ].get('selectedProject'),
  isModalOpen: state[ MODULE_NAME ].get('isModalOpen'),
  isShowInactive: state[ MODULE_NAME ].get('isShowInactive'),
  transferToInactive: state[ MODULE_NAME ].get('transferToInactive')
});


export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
