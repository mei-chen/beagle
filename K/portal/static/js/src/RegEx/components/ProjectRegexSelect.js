import React from 'react';
import { connect } from 'react-redux';
import ProjectSelect from 'base/components/ProjectSelect';
import { Row, FormGroup, ControlLabel, Col, ButtonToolbar, Button } from 'react-bootstrap';
import { convertObjectsToOptions } from 'base/utils/misc';
import Select from 'react-select';
import 'react-select/dist/react-select.css';
import { MODULE_NAME } from 'RegEx/constants';

const RegExSelect = ({ regexes, onChange, selectedRegEx }) => {
  const getOptions = () => {
    const options = [];
    regexes.every(rgx => options.push({ label: `${rgx.name}: ${rgx.content}`, value: rgx.id }));
    return options;
  };
  return (
    <FormGroup>
      <Select
        name="rgx-select"
        value={selectedRegEx.get('id') || ''}
        options={getOptions()}
        onChange={onChange}
      />
    </FormGroup>
  )
};

const ProjectRegexSelect = ({ regexes, onProjectChange, onRgxChange, selectedRegEx, setModalOpen }) =>
  <span>
    <div className="label-wrapper">
      <ControlLabel>RegExs</ControlLabel>
    </div>
    <div className="form-flex-half-wrapper">
      <Col xs={6}>
        <RegExSelect
          onChange={onRgxChange}
          regexes={regexes}
          selectedRegEx={selectedRegEx}
        />
      </Col>
      <Col xs={6}>
        <ButtonToolbar>
          <Button
            onClick={() => setModalOpen('create', true)}
          >
            Create New RegEx
          </Button>
          <Button
            onClick={() => setModalOpen('edit', true)}
            disabled={!selectedRegEx.size}
          >
            Edit RegEx
          </Button>
          <Button
            bsStyle="danger"
            onClick={() => setModalOpen('delete', true)}
            disabled={!selectedRegEx.size}
          >
            Delete RegEx
          </Button>
        </ButtonToolbar>
      </Col>
    </div>
    <Row className="no-margin-row">
      <Col xs={6}>  
        <ProjectSelect
          onChange={onProjectChange}
          displayAllOption={false}
        />
      </Col>
    </Row>
  </span>;


export default connect(
  (state) => ({
    regexes: state[ MODULE_NAME ].get('regexes'),
    selectedRegEx: state[ MODULE_NAME ].get('selectedRegEx')
  })
)(ProjectRegexSelect);
