import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import BatchController from "ProjectManagement/components/BatchController";
import { projectPropType } from "ProjectManagement/propTypes";
import { MODULE_NAME } from 'ProjectManagement/constants';


const ProjectManagementPanel = ({ selectedProject }) => {
  if (!selectedProject.size) return null;
  return (
    <div>
      <h4>{selectedProject.get('name')}</h4>
      <BatchController project={selectedProject.get('id')}/>
    </div>
  );
};

ProjectManagementPanel.propTypes = {
  projects: PropTypes.arrayOf(projectPropType)
};


export default connect(
  (state) => ({
    selectedProject: state[ MODULE_NAME ].get('selectedProject')
  })
)(ProjectManagementPanel);
