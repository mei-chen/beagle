/* NPM Modules */
import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import { Typeahead } from 'react-typeahead';
import uuidV4 from 'uuid/v4';

// App
import log from 'utils/logging';
import Tag from 'common/components/Tag.jsx'
import {
  addBulkTags,
  approveBulkTags,
  deleteBulkTags
} from 'report/redux/modules/report';

/* Constants */
require('utils/constants.js');

/* Style */
const styles = require('./styles/BulkTagTools.scss');

var BulkTagTools = React.createClass({

  propTypes: {
    user: React.PropTypes.object.isRequired,
    sentences: React.PropTypes.array.isRequired,
  },

  onDuplicateAdd() {
    log('DUPLICATE ADD');
  },

  /*
  * given an array of sentences, find the annotation object matching
  * the specified token
  */
  findAnnotation(token) {
    //each sentence WILL have amongst it, the desired tag to be deleted. Just look at the first one.
    //Find the first instance of the desired annotation to delete
    const { sentences } = this.props;
    var annotation = sentences[0].annotations.find(a => a.label.toLowerCase() === token.toLowerCase());

    if (!annotation) {
      log.error(`requested bulk tag delete for tag: "${token}" failed. Unable to find "${token}" in annotations object`);
      return
    }
    return annotation
  },

  getManualAnnotationTokens() {
    var annotationTokens = [];
    if (this.props.bulkAnnotations) {
      annotationTokens = this.props.bulkAnnotations.map(annotation => {
        return (
          <Tag
            learners={this.props.learners}
            key={uuidV4()}
            name={annotation.label.toLowerCase()}
            onTokenRemove={this.onTokenRemove}
            suggested={annotation.suggested && annotation.class === 'S'}
            onTokenApprove={this.onTokenApprove}
          />
        )
      });
    }
    return annotationTokens;
  },

  handleKeyPress(e) {
    if (e.key === 'Enter' && this.refs.bulkTags.state.entryValue !== '') {  // enter pressed
      const tag = this.refs.bulkTags.state.entryValue;
      this.refs.bulkTags.setEntryText('');  //clear input element
      this.onTokenAdd(tag);
    }
  },

  onOptionSelected(option) {
    this.onTokenAdd(option);
    this.refs.bulkTags.setEntryText('');   //clear input element
  },

  // Add bulk sentences only requires a string because you can only add manual tokens which needs no type/sublabel/party on the backend
  addBulkSentenceTag(token) {
    const { dispatch } = this.props;
    const sentenceIdxs = _.map(this.props.sentences, 'idx');
    const annotation = {};
    //build the new annotation object to bulk create
    annotation['type'] = window.MANUAL_TAG_TYPE;
    annotation['label'] = token;

    dispatch(addBulkTags(sentenceIdxs, [annotation]));
  },

  approveBulkSentenceTag(token) {
    const { dispatch } = this.props;
    const sentenceIdxs = _.map(this.props.sentences, 'idx');
    const annotation = this.findAnnotation(token);

    dispatch(approveBulkTags(sentenceIdxs, [annotation]));
  },

  deleteBulkSentenceTag(token) {
    const { dispatch } = this.props;
    const sentenceIdxs = _.map(this.props.sentences, 'idx');
    const annotation = this.findAnnotation(token);

    dispatch(deleteBulkTags(sentenceIdxs, [annotation]));
  },

  onTokenAdd(token) {
    this.addBulkSentenceTag(token);
  },

  onTokenRemove(token) {
    this.deleteBulkSentenceTag(token);
  },

  onTokenApprove(token) {
    this.approveBulkSentenceTag(token);
  },

  render() {
    const { isBulkTagRequesting, user } = this.props;
    const options = user.tags || [];
    const customClasses = {
      token: isBulkTagRequesting ? 'tags-bulk-requesting' : ''
    }

    return (
      <div className={styles.tagTools}>
        <div className="manual-tags">
          {this.getManualAnnotationTokens()}
          <Typeahead
            ref="bulkTags"
            maxVisible={5}
            options={options}
            placeholder="Enter bulk tags here..."
            onKeyDown={this.handleKeyPress}
            onOptionSelected={this.onOptionSelected}
            customClasses={customClasses}
          />
        </div>
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
  // In case user creates a bulk tag and immediately deletes, if it hasn't finished creating in the server
  // it creates an error. This is not ideal as if a user creates 2 bulk tags, first response will set it to false
  // which means user can delete the second tag, which will result in an error.
    isBulkTagRequesting: state.report.get('isBulkTagRequesting'),
    bulkAnnotations: state.report.get('bulkAnnotations').toJS(),
    learners: state.report.get('learners').toJS(),
  }
};

export default connect(mapStateToProps)(BulkTagTools);
