import { Map } from 'immutable';
import React from 'react';
import { connect } from 'react-redux';
import {
    FormGroup,
    ControlLabel,
    Glyphicon,
    OverlayTrigger,
    Popover,
    Grid,
    Col,
    Row,
    ButtonToolbar,
    Button
} from 'react-bootstrap';
import Select from 'react-select';
import 'react-select/dist/react-select.css';
import { MODULE_NAME } from 'KeyWords/constants';

const colStyle = {
  paddingRight: '0px',
  paddingLeft: '0px',
};

const listIconStyle = {
  fontSize: '18px',
  textAlign: 'center',
  paddingTop: '30px'
}

const KeywordListSelect = ({ keywordlists, onChange, selectedKeywordList, setModalOpen }) => {
  const getOptions = () => {
    const options = [];
    keywordlists.every(kwl => options.push({ label: `${kwl.name}`, value: `${kwl.name}` }));
    return options;
  };

  const keywordsInList = () => {
    const keywords = selectedKeywordList.get('keywords') || [Map({ content: 'No keywords', uuid: 'No keywords' })];
    return <Popover id="info-popover" title="Keywords">
      {keywords.map(keyword => {
        return <div style={{fontSize: 10}} key={keyword.get('uuid')}>
          {keyword.get('content')}
        </div>
      })}
    </Popover>;
  }
  return (
    <FormGroup>
      <Col style={colStyle} xs={7} md={7}>
      <ControlLabel>Keyword Lists</ControlLabel>
      <Select
        name="kwls-select"
        value={selectedKeywordList.get('name') || ''}
        options={getOptions()}
        onChange={onChange}
      />
      </Col>
      <Col style={colStyle} xs={1} md={1}>
      <div style={listIconStyle}>
        <OverlayTrigger trigger={['hover', 'focus']} placement="right" overlay={keywordsInList()}>
          <Glyphicon glyph="list-alt"/>
        </OverlayTrigger>
      </div>
      </Col>
      <Col xs={4} md={4}>
      <div style={listIconStyle}>
        <ButtonToolbar>
          <Button
            bsSize="small"
            onClick={() => setModalOpen('edit', true)}
            disabled={!selectedKeywordList.size}
          >
            Edit Keyword list
          </Button>
          <Button
            bsSize="small"
            bsStyle="danger"
            onClick={() => setModalOpen('delete', true)}
            disabled={!selectedKeywordList.size}
          >
            Delete Keyword list
          </Button>
        </ButtonToolbar>
        </div>
      </Col>
    </FormGroup>
  )
};


export default KeywordListSelect;
