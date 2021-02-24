import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { Grid, Col } from 'react-bootstrap';
import SentenceSearchController from 'SentenceSearch/components/SentenceSearchController';
import PreviewSentencesPopup from 'SentenceSearch/components/PreviewSentencesPopup';

import {
  setModalOpen
} from 'SentenceSearch/redux/actions';

import { MODULE_NAME } from 'SentenceSearch/constants';

import "../scss/ContentComponent.scss"

class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { isModalOpen, setModalOpen, selectedReport } = this.props;

    return (
        <div>
          <Grid>
            <Col xs={12} md={12}>
              <SentenceSearchController />
            </Col>
          </Grid>
          <PreviewSentencesPopup
            isOpen={isModalOpen.get('preview')}
            report={selectedReport}
            onClose={() => setModalOpen('preview', false)}
            title="Report Preview"
          />
        </div>
    );
  }
}

const mapDispatchToProps = dispatch => bindActionCreators({
  setModalOpen
}, dispatch);

const mapStateToProps = state => ({
  isModalOpen: state[ MODULE_NAME ].get('isModalOpen'),
  selectedReport: state[ MODULE_NAME ].get('selectedReport')
});

export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
