import React from 'react';
import pt from 'prop-types';
import { Panel, Button, Grid, Col, ButtonToolbar } from 'react-bootstrap';

const KeywordListPanel = ({ recommendCall, currentWord, simModel, setModalOpen, selectedKeywordList, selectedSimModel, recommendations }) =>
  <Panel>
    <Grid>
      <Col xs={6} md={6}>
        <ButtonToolbar>
          <Button
            bsSize="small"
            onClick={() => recommendCall(currentWord, simModel)}
            disabled={!selectedSimModel.size || currentWord === ''}
          >
            Recommend
          </Button>
          <Button
            bsSize="small"
            onClick={() => setModalOpen('create', true)}
            disabled={!recommendations.size}
          >
            Create New Keyword list
          </Button>
        </ButtonToolbar>
      </Col>
      <Col xs={6} md={6}>
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
      </Col>
    </Grid>
  </Panel>;

KeywordListPanel.propTypes = {
  setModalOpen: pt.func
};

export default KeywordListPanel;
