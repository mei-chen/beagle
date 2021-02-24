import React from "react";
import { Table } from "react-bootstrap";
import { projectPropType } from "ProjectManagement/propTypes";


const ProjectsListRow = ({ project, selectProject, deselectProject, active, isShowInactive }) => {
  const Tr = ({ children }) => {
    if (isShowInactive) {
      return <tr>{children}</tr>
    } else {
      return (
        <tr className={`row-clickable ${active ? 'active': ''}`}
            onClick={active ? () => deselectProject() : () => selectProject(project)}>
          {children}
        </tr>
      )
    }
  };
  const ContentFile = () => {
    if (project.archive.content_file) {
      return <td><a href={project.archive.content_file}>{project.archive.created_at}</a></td>
    } else {
      return <td>{project.archive.created_at}</td>
    }
  };
  return (
    <Tr>
      <td>{project.id}</td>
      <td>{project.name}</td>
      <td>{project.status_verbose}</td>
      <td>{project.owner_username}</td>
      <td>{project.batch_count}</td>
      { isShowInactive && <ContentFile /> }
    </Tr>
  )
};


const ProjectsList = ({ projects, selectProject, deselectProject, selectedProject, isShowInactive }) =>
  <Table striped bordered condensed hover responsive>
    <thead>
    <tr>
      <th>Project ID</th>
      <th>Project Name</th>
      <th>Status</th>
      <th>Owner</th>
      <th>Batches</th>
      {isShowInactive && <th>Archive file download</th>}
    </tr>
    </thead>
    <tbody>
    {
      projects.map((project) => (
        <ProjectsListRow
          key={project.resource_uri}
          project={project}
          selectProject={selectProject}
          deselectProject={deselectProject}
          active={selectedProject.get('id') === project.id}
          isShowInactive={isShowInactive}
        />
      ))
    }
    </tbody>
  </Table>;

export default ProjectsList;
