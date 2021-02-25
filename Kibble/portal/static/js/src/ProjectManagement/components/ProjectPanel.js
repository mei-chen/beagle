import React from 'react';
import pt from 'prop-types';
import {
  Panel,
  Button,
  Grid,
  Col,
  ButtonToolbar,
  Glyphicon,
  OverlayTrigger,
  Tooltip
} from 'react-bootstrap';


const InfoTooltip = (
  <Tooltip id="tooltip-info">
    To rename or archive a project select the project in the table below.
  </Tooltip>
);

const ProjectPanel = ({ setModalOpen, selectedProject, setShowInactive, isShowInactive }) =>
  <Panel>
    <Grid>
      <Col xs={12} md={12}>
        <ButtonToolbar>
          <Button
            bsSize="small"
            onClick={() => setModalOpen('create', true)}
          >
            Create New Project <i className="far fa-plus"></i>
          </Button>

          <Button
            bsSize="small"
            onClick={() => setModalOpen('edit', true)}
            disabled={!selectedProject.size || isShowInactive}
          >
            Edit Project <i className="fal fa-edit"></i>
          </Button>

          <Button
            bsSize="small"
            onClick={() => setModalOpen('collaborators', true)}
            disabled={!selectedProject.size || isShowInactive}
          >
            Manage Collaborators <i className="fal fa-users"></i>
          </Button>

          <Button
            bsSize="small"
            bsStyle="danger"
            onClick={() => setModalOpen('archive', true)}
            disabled={!selectedProject.size || isShowInactive}
          >
            Archive Project <i className="fal fa-archive"></i>
          </Button>

          <Button
            bsSize="small"
            onClick={() => setShowInactive(!isShowInactive)}
            active={isShowInactive}
          >
            Show Inactive <i className="fal fa-eye-slash"></i>
          </Button>

          <div className="pull-right" style={{marginTop: 5, fontSize: 18}}>
            <OverlayTrigger trigger={['hover', 'focus']} placement="top" overlay={InfoTooltip}>
              <Glyphicon glyph="info-sign"/>
            </OverlayTrigger>
          </div>

        </ButtonToolbar>
      </Col>
    </Grid>
  </Panel>;

ProjectPanel.propTypes = {
  setModalOpen: pt.func
};

export default ProjectPanel;
