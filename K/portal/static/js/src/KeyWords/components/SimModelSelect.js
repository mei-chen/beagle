import React from 'react';
import { connect } from 'react-redux';
import { Grid, Col, Row, Button, ButtonToolbar, FormGroup, ControlLabel } from 'react-bootstrap';
import Select from 'react-select';
import 'react-select/dist/react-select.css';
import { MODULE_NAME } from 'KeyWords/constants';


const formSelectStyle = {
  background: '#f7f7f7',
  padding: '15px 0',
  marginBottom: 30,
  borderRadius: 5
};

const SimModelSelect = ({ simmodels, onChange, selectedSimModel, makeRecommendations, currentWord }) => {
  const getOptions = () => {
    const options = [];
    simmodels.every(smm => options.push({ label: `${smm.name}`, value: `${smm.api_name}` }));
    return options;
  };
  return (
    <div className="input-wrapper">
      <Select
        wrapperStyle={{width:'100%'}}
        style={{borderRadius:'0px',border:'1px solid #a9a9a9'}}
        name="smm-select"
        placeholder="Select Relatedness Models..."
        value={selectedSimModel.get('api_name') || ''}
        options={getOptions()}
        onChange={onChange}
      />
      <ButtonToolbar>
        <Button
          className="add-button"
          onClick={() => makeRecommendations(currentWord, selectedSimModel)}
          disabled={!selectedSimModel.size || currentWord === ''}
        >
          Recommend
        </Button>
      </ButtonToolbar>
    </div>
  )
};

export default SimModelSelect;
