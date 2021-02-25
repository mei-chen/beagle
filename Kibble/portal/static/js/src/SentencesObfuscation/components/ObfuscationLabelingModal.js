import React from "react";
import { Map, List } from 'immutable';
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import { Modal, Grid, Row, Col, Button, ButtonToolbar, ToggleButton, ToggleButtonGroup } from "react-bootstrap";
import {
  markSentence,
  markAllSentences,
  cancelLabeling,
  doneLabeling
} from 'SentencesObfuscation/redux/actions';
import { MODULE_NAME } from 'SentencesObfuscation/redux/constants';
import { getFromServer as getSettingsFromServer } from 'Settings/redux/modules/settings.js'
class ReportRow extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      obf_tool: this.props.obfTool
    }

    this.onMethodChange = this.onMethodChange.bind(this);
  }

  componentWillReceiveProps(nexProps) {
    if(this.props.obfTool != nexProps.obfTool){
      this.setState({
        obf_tool: nexProps.obfTool
      })
    }
  }

  onMethodChange(e) {
    const { reportId, sentenceIdx, markSentence } = this.props;
    markSentence(reportId,sentenceIdx,e);
  }

  render() {
    return (
      <Row key={this.props.sentenceIdx} className="row-style">
        <Col className="col-style" xs={3} md={3} sm={3}>{this.props.reportName}</Col>
        <Col className="col-style" xs={7} md={7} sm={7}>{this.props.report.sentence}</Col>
        <Col className="flex-col" xs={2} md={2} sm={2}>
          <div>
            <ButtonToolbar>
              <ToggleButtonGroup
                vertical
                type="radio"
                name="options"
                value={this.state.obf_tool}
                onChange={this.onMethodChange}
              >
                <ToggleButton value={'black_out'}>Redact</ToggleButton>
                <ToggleButton value={'string'}>Obfuscate</ToggleButton>
                <ToggleButton value={'highlight'}>Highlight</ToggleButton>
                <ToggleButton value={'none'}>None</ToggleButton>
              </ToggleButtonGroup>
            </ButtonToolbar>
          </div>
        </Col>
      </Row>
    )
  }
}

class ObfuscationModal extends React.Component {
  constructor(props) {
    super(props);

    this.markAllAs = this.markAllAs.bind(this)
  }

  markAllAs(all_reports, method) {
    const {
      selected_reports,
      markAllSentences
    } = this.props;

    var gatherd_data = new Map({});
    selected_reports.map(selcted_report_id => {
      const report_content = all_reports.find(report => {
        return report.id === selcted_report_id;
      });
      JSON.parse(report_content.json||'[]').map((sentence,idx) => {
        gatherd_data = gatherd_data.setIn([selcted_report_id,idx], method);
      })
    })

    markAllSentences(gatherd_data);
  }

  render() {
    const {
      isOpen,
      title,
      selected_reports,
      sentences_reports,
      keywords_reports,
      regex_reports,
      onClose,
      markSentence,
      cancelLabeling,
      doneLabeling,
      selcetedSentences,
      getSettingsFromServer
    } = this.props;

    const all_reports = keywords_reports.concat(regex_reports.concat(sentences_reports));

    return (
      <Modal show={isOpen} bsSize="large" onHide={onClose}>

        <Modal.Header closeButton={true}>
          <Modal.Title>{title}</Modal.Title>
        </Modal.Header>

        <Modal.Body className="scrollable-body">
          <Grid>
            <Row className="row-style head">
                <Col className="col-style" xs={3} md={3} sm={3}><h4>Report</h4></Col>
                <Col className="col-style" xs={7} md={7} sm={7}><h4>Sentence</h4></Col>
                <Col className="flex-col" xs={2} md={2} sm={2}>
                  <div>
                    <h4>Label</h4>
                    Mark all:
                    <ButtonToolbar>
                      <ToggleButtonGroup
                        vertical
                        bsSize="xsmall"
                        type="radio"
                        name="options"
                        onChange={(e) => this.markAllAs(all_reports,e)}
                      >
                        <ToggleButton value={'black_out'}>Redact</ToggleButton>
                        <ToggleButton value={'string'}>Obfuscate</ToggleButton>
                        <ToggleButton value={'highlight'}>Highlight</ToggleButton>
                        <ToggleButton value={'none'}>None</ToggleButton>
                      </ToggleButtonGroup>
                    </ButtonToolbar>
                  </div>
                </Col>
            </Row>
            {all_reports.map(report => {
              if (selected_reports.contains(report.id)) {
                return JSON.parse(report.json||'[]').map((report_idx, index) => {
                  return (<ReportRow
                    key={index}
                    sentenceIdx={index}
                    report={report_idx}
                    reportName={report.name}
                    reportId={report.id}
                    markSentence={markSentence}
                    obfTool={selcetedSentences[report.id] ? selcetedSentences[report.id][index] : null}
                  />)
                })
              }
            })}
          </Grid>
        </Modal.Body>

        <Modal.Footer>
          <Button bsStyle="danger" onClick={() => { onClose(); cancelLabeling() }}>Cancel</Button>
          <Button
            bsStyle="primary"
            onClick={() => { onClose(); doneLabeling(); getSettingsFromServer() }}
          >
            Done
          </Button>
        </Modal.Footer>

      </Modal>
    )
  }
}

export default connect(
  (state) => ({
    selcetedSentences: state[ MODULE_NAME ].get('selceted_sentences').toJS()
  }),
  (dispatch) => bindActionCreators({
    markSentence,
    markAllSentences,
    cancelLabeling,
    doneLabeling,
    getSettingsFromServer
  }, dispatch)
)(ObfuscationModal);
