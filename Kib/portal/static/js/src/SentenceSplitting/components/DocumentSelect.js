import React, { Component } from "react";
import types from 'prop-types';
import { connect } from "react-redux";
import {
  ListGroup,
  ListGroupItem,
  Col,
  Glyphicon
} from "react-bootstrap";
import DebounceInput from "react-debounce-input";
import { SwitchSelectState } from 'base/components/DefaultButtons';
import { MODULE_NAME } from 'SentenceSplitting/redux/constants';


const DocumentListItemDownloadLink = ({ docId }) =>
  <div className="pull-right">
    <Glyphicon glyph="download-alt"/>
    <a className="ml-3" href={`${window.CONFIG.API_URLS.downloadSentences}?document=${docId}`}>CSV</a>
    <a className="ml-3" href={`${window.CONFIG.API_URLS.downloadSentences}?document=${docId}&json=1`}>JSON</a>
  </div>;


const DocumentListItem = ({ doc: { name, id, tags }, updateDocumentIds, checked, isLocked }) =>
  <ListGroupItem onClick={() => !isLocked && updateDocumentIds(id)}
                 disabled={isLocked}>
    {name} <span style={{color: 'red'}}>{ !tags.length && '(dirty)'}</span>
    <div className="pull-right">
      <Glyphicon glyph={checked ? 'check' : 'unchecked'}/>
    </div>
  </ListGroupItem>;

DocumentListItem.propTypes = {
  doc: types.shape({}),
  updateDocumentIds: types.func.isRequired,
  checked: types.bool,
  isLocked: types.bool
};


class DocumentSelect extends Component {
  constructor(props) {
    super(props);
    this.state = {
      searchTerm: ''
    };

    this.filterChange = (ev) => this.setState({ searchTerm: ev.target.value.toLowerCase() });
    this.getFilteredDocuments = this.getFilteredDocuments.bind(this);
    this.selectAll = this.selectAll.bind(this);

  }

  getFilteredDocuments() {
    const { searchTerm } = this.state;
    return this.props.documents.filter((document) => {
      return !searchTerm || document.name.toLowerCase().indexOf(searchTerm) !== -1
    })
  }

  selectAll(switchTo) {
    if (!switchTo) {
      this.props.updateDocumentIds();
      return;
    }

    this.props.updateDocumentIds(
      this.getFilteredDocuments().map(doc => doc.id)
    )
  }

  renderUnprocessedDocumentList() {
    const documents = this.getFilteredDocuments();
    return documents.map(doc =>
      <DocumentListItem
        doc={doc}
        key={doc.uuid}
        updateDocumentIds={this.props.updateDocumentIds}
        checked={this.props.isDocumentSelected(doc.id) === true}
        isLocked={this.props.lockedDocuments.includes(doc.id) === true}
      />
    )
  }

  renderProcessedDocumentList() {
    return this.props.hasSentences.map(doc =>
      <ListGroupItem key={doc.uuid}>
        {doc.name}
        <DocumentListItemDownloadLink docId={doc.id}/>
      </ListGroupItem>
    )
  }

  render() {
    return (
      <div>
        <Col xs={6} md={6}>
          <strong>Unprocessed Documents</strong>
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
            onSelectAll={() => this.selectAll(true)}
            onDeselectAll={() => this.selectAll(false)}
          />
          <ListGroup className="file-list">
            {this.renderUnprocessedDocumentList()}
          </ListGroup>

        </Col>

        <Col xs={6} md={6}>
          <strong>Processed Documents</strong>
          <ListGroup className="file-list">
            {this.renderProcessedDocumentList()}
          </ListGroup>
        </Col>
      </div>
    )
  }
}

export default connect(
  (state) => ({
    documents: state[ MODULE_NAME ].get('documents'),
    hasSentences: state[ MODULE_NAME ].get('hasSentences'),
    lockedDocuments: state[ MODULE_NAME ].get('lockedDocuments')
  })
)(DocumentSelect)
