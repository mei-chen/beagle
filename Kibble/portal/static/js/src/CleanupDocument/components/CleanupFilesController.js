import React from 'react';
import PropTypes from 'prop-types';
import { batchPropType } from 'BatchManagement/propTypes';
import {
  ListGroup,
  ListGroupItem,
  Grid,
  Col,
  Button,
  Glyphicon,
  Panel,
  ButtonGroup,
  Label
} from 'react-bootstrap';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import DebounceInput from 'react-debounce-input';
import { updateFilter, setState, blockDocs } from 'CleanupDocument/redux/actions';
import { postCleanup } from 'base/redux/modules/cleanup';
import { SwitchSelectState } from 'base/components/DefaultButtons';
import { filterObjects } from 'base/utils/misc';
import { MODULE_NAME } from 'CleanupDocument/constants'

class DocListItem extends React.Component {
  constructor(props) {
    super(props);
    this.check = () => {
      const { setState, doc, state } = this.props;
      setState(doc.id, !state);
    }
  }

  renderDownloadLinks({ cleaned_txt, cleaned_docx }) {
    if (!(cleaned_txt || cleaned_docx)) return null;
    return (
      <div className="btn-group mr-3">
        <Glyphicon glyph="download-alt"/>
        {cleaned_txt && <a className="ml-3" href={cleaned_txt}>txt</a>}
        {cleaned_txt && <a className="ml-3" href={cleaned_docx}>docx</a>}
      </div>
    )
  }

  renderTags() {
    const { doc } = this.props;
    return doc.tags.map((tag, i) => (
      <Label key={i} style={{ marginRight: 2, display: 'inline-block' }}>{tag}</Label>
    ));
  }

  render() {
    const { doc, state, disabled } = this.props;
    return (
      <ListGroupItem disabled={disabled}>
        <div>
          {doc.name}
          <div className="pull-right">
            {this.renderDownloadLinks(doc)}
            <Glyphicon
              glyph={state === true ? 'check' : 'unchecked'}
              style={{cursor: 'pointer'}}
              onClick={this.check} disabled={disabled}
            />
          </div>
        </div>
        <div>
          {this.renderTags()}
        </div>
      </ListGroupItem>
    );
  }
}

DocListItem.propTypes = {
  doc: PropTypes.object.isRequired,
  state: PropTypes.bool.isRequired,
  disabled: PropTypes.bool.isRequired,
  setState: PropTypes.func.isRequired
};

class CleanupFilesController extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedDoc: null,
      searchTerm: '',
    };

    this.docChange = doc => this.setState({ selectedDoc: doc });
    this.filterChange = ev => this.setState({
      searchTerm: ev.target.value
    });

    this.getFilteredDocs = this.getFilteredDocs.bind(this);
    this.switchSelectedState = this.switchSelectedState.bind(this);
    this.doCleanup = this.doCleanup.bind(this);
  }

  getFilteredDocs() {
    const { docs } = this.props;
    const { searchTerm } = this.state;
    return filterObjects(docs, 'name', searchTerm);
  }

  switchSelectedState(state = true) {
    const docs = this.getFilteredDocs();
    for (const doc of docs) {
      this.props.setState(doc.id, state)
    }
  }

  doCleanup() {
    const { toolsState, postCleanup, blockDocs } = this.props;
    const docState = this.props.docState.toJS();
    const selectedTools = toolsState.map(item => item.tool);
    const selectedDocs = Object.keys(docState).filter((item) => {
      return (docState[item] === true);
    });
    if (selectedDocs.length) {
      blockDocs(selectedDocs);
      postCleanup({ sequence: selectedTools, documents: selectedDocs });
    }
  }

  renderListOfDocs() {
    const { selectedDoc } = this.state;
    const { docState, blockedDocs, setState } = this.props;
    const docs = this.getFilteredDocs();
    return docs.map((doc) => (
      <DocListItem
        key={doc.id}
        doc={doc}
        active={doc.id === selectedDoc}
        setState={setState}
        state={docState.get(doc.id) === true}
        disabled={blockedDocs.includes(doc.id) === true}
        handleSelect={this.docChange}
      />
    ));
  }

  isBulkDownloadAvailable() {
    return this.props.docs.some(doc => !!doc.tags.length);
  }

  downloadUri(batchId, plain) {
    let uri = window.CONFIG.API_URLS.batchDownloadClean + '?batch=' + batchId;
    if (plain) {
      uri += '&plaintext=1';
    }
    return uri;
  }

  cleanupButtonDisabled() {
      const { docState, toolsState } = this.props;
      let toolsSelected = toolsState.count() === 0;
      let documentSelected = Object.values(docState.toJS()).filter(item => item).length === 0;
      return (toolsSelected || documentSelected);
  }

  render() {
    const filesDocsGroup = (
      <div className="project-list-selector">
        <ListGroup className="cleanup-filelist scrollable">
          {this.renderListOfDocs()}
        </ListGroup>
      </div>
    );

    return (
      <Grid>
        <Col xs={12} md={12}>
          <Panel>
            <Button onClick={this.doCleanup} disabled={this.cleanupButtonDisabled() === true}>
              { this.cleanupButtonDisabled() === true ? 'Select a cleanup tool first' : 'Cleanup' }
            </Button>
            {this.isBulkDownloadAvailable() &&
            <ButtonGroup className="pull-right">
              <a className="btn btn-default"
                 href={this.downloadUri(this.props.batchId, true)}>
                <Glyphicon glyph="download-alt"/> All txt
              </a>
              <a className="btn btn-default"
                 href={this.downloadUri(this.props.batchId, false)}>
                <Glyphicon glyph="download-alt"/> All docx
              </a>
            </ButtonGroup>
            }
          </Panel>
          <DebounceInput
            type="text"
            className="search-projects"
            name="search-projects"
            placeholder="Search"
            minLength={2}
            debounceTimeout={100}
            onChange={this.filterChange}
          />
          <SwitchSelectState
            onSelectAll={() => this.switchSelectedState(true)}
            onDeselectAll={() => this.switchSelectedState(false)}
          />
          {filesDocsGroup}
        </Col>
      </Grid>
    );
  }
}

CleanupFilesController.propTypes = {
  batchId: PropTypes.number.isRequired
};

const mapStateToProps = (state) => {
  return {
    docs: state[ MODULE_NAME ].get('docs'),
    docState: state[ MODULE_NAME ].get('docState'),
    blockedDocs: state[ MODULE_NAME ].get('blockedDocs'),
    docFilterValue: state[ MODULE_NAME ].get('docFilterValue'),
    toolsState: state[ MODULE_NAME ].get('toolsState')
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    updateFilter, setState, postCleanup, blockDocs
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(CleanupFilesController);
