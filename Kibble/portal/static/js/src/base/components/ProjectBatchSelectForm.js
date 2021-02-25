import React from 'react';
import pt from 'prop-types';
import { Col, Row } from 'react-bootstrap';
import BatchSelect from 'base/components/BatchSelect';
import ProjectSelect, { PROJECT_NOT_SELECTED } from 'base/components/ProjectSelect';
import { batchPropType } from 'BatchManagement/propTypes';
import { projectPropType } from "ProjectManagement/propTypes";


const formSelectStyle = {
  background: '#f7f7f7',
  padding: '15px 0',
  marginBottom: 30,
  border: '1px solid lightgray',
  borderRadius: 5,
  zIndex: 10,
  position: 'relative',
};


class ProjectBatchSelectForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      showBatchSelect: false,
      doClear: false
    };
    this.doClearDone = () => this.setState({ doClear: false });
    this.onProjectChange = this.onProjectChange.bind(this);
  }

  onProjectChange(val) {
    this.setState({ showBatchSelect: val > PROJECT_NOT_SELECTED, doClear: true });
    this.props.onProjectChange(val);
  }

  render() {
    return (
      <Row style={formSelectStyle}>
        <Col xs={6}>
          <ProjectSelect
            onChange={this.onProjectChange}
            title={this.props.projectTitle}
            displayAllOption={this.props.displayAllOption}
          />
        </Col>

        <Col xs={6}>
          <BatchSelect
            onChange={this.props.onBatchChange}
            display={this.state.showBatchSelect}
            batches={this.props.batches}
            title={this.props.batchTitle}
            doClear={this.state.doClear}
            doClearDone={this.doClearDone}
          />
        </Col>
      </Row>
    )
  }
}

ProjectBatchSelectForm.propTypes = {
  onBatchChange: pt.func.isRequired,
  onProjectChange: pt.func.isRequired,
  batchTitle: pt.string,
  projectTitle: pt.string,
  displayAllOption: pt.bool
};

ProjectBatchSelectForm.defaultProps = {
  batchTitle: 'Batches',
  projectTitle: 'Projects',
  displayAllOption: true
};

export default ProjectBatchSelectForm;
