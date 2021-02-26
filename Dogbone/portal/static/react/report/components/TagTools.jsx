import React from 'react';
import { connect } from 'react-redux';
import { Typeahead } from 'react-typeahead';
import _ from 'lodash';
import uuidV4 from 'uuid/v4';

import log from 'utils/logging';
import Tag from 'common/components/Tag.jsx'
import styles from './styles/TagTools.scss';
import {
  addTag,
  deleteTag,
  approveSuggestedTag
} from 'report/redux/modules/report';

require('utils/constants.js');


var TagTools = React.createClass({

  propTypes: {
    user: React.PropTypes.object.isRequired,
    sentence: React.PropTypes.object.isRequired,
  },

  /**
   * getAnnotationTokens()
   * ------------------------
   * Takes the annotations array of form (eg):
    * [
    *   {
    *     approved: true,
    *     classifier_id: null,
    *     label: "RESPONSIBILITY",
    *     party: "you",
    *     sublabel: "ABSOLUTE_RESPONSIBILITY",
    *     type: "A",
    *     user: null
    *   },
    *   {
    *     approved: true,
    *     classifier_id: null,
    *     label: "hank",
    *     party: null,
    *     sublabel: null,
    *     type: "M",
    *     user: "cian"
    *   }
    * ]
   * and returns the token array of form:
   * [  "RESPONSIBILITY", "hank" ]
   */
   // This was modified as react-type ahead changed from requiring a json object
   // To requiring a single string

  getManualAnnotationTokens() {
    var annotationTokens = [];
    if (this.props.sentence.annotations) {
      annotationTokens = this.props.sentence.annotations.map(annotation => {
        return (
          <Tag
            learners={this.props.learners}
            key={uuidV4()}
            name={annotation.label.toLowerCase()}
            suggested={!annotation.approved && annotation.type === 'S'}
            onTokenRemove={this.onTokenRemove}
            onTokenApprove={this.onTokenApprove}
          />
        )
      });
    }
    return annotationTokens;
  },


  addSentenceTag(tag) {
    const { dispatch } = this.props;
    log(`addSentenceTag: ${tag}`);

    dispatch(addTag(this.props.sentence.idx, tag));
  },

  deleteSentenceTag(annotation) {
    const { dispatch } = this.props;
    log(`deleteSentenceTag: ${annotation.label}`);

    dispatch(deleteTag(this.props.sentence.idx, annotation));
  },

  approveSuggestedTag(annotation) {
    const { dispatch } = this.props;
    log(`approveSuggestedTag: ${annotation.label}`);

    dispatch(approveSuggestedTag(this.props.sentence.idx, annotation));
  },

  getAnnotationFromSentence(token) {
    const { sentence } = this.props;
    // Match the removed token with it's annotation object
    const annotation = (sentence.annotations || []).find(a => {
      return a.label.toLowerCase() === token.toLowerCase()
    });

    if (!annotation) {
      log.error(`requested tag delete for tag: "${token}" failed. Unable to find "${token}" in sentence.annotations object`);
      return
    }
    return annotation
  },

  handleKeyPress(e) {
    if (e.key === 'Enter' && this.refs.tags.state.entryValue !== '') {  // enter pressed
      const tag = this.refs.tags.state.entryValue;
      this.refs.tags.setEntryText('');  //clear input element
      this.onTokenAdd(tag);
    }
  },

  onOptionSelected(option) {
    this.onTokenAdd(option);
    this.refs.tags.setEntryText('');   //clear input element
  },

  /**
   * onTokenAdd
   *
   * This is the hook that gets called on adding a token by creating it on the
   * fly. This is the hook that gets called when you type in a new tag.
   *
   * @param {string} token
   */
  onTokenAdd(token) {
    log('onTokenAdd:', token);
    this.addSentenceTag(token);
  },

  onTokenRemove(token) {
    log('onTokenRemove: ', token);
    const annotation = this.getAnnotationFromSentence(token);
    // Delete the tag
    this.deleteSentenceTag(annotation);
  },

  onTokenApprove(token) {
    log('onTokenApprove: ', token);
    const annotation = this.getAnnotationFromSentence(token);
    // Delete the tag
    this.approveSuggestedTag(annotation);
  },

  render() {
    const userTags = this.props.user.tags || [];
    const sentTags = (this.props.sentence.annotations || []).map(a => a.label);
    const options = _.sortBy(_.difference(userTags, sentTags));
    return (
      <div className={styles.tagTools} id="eb-step3">
        <div className="manual-tags">
          {this.getManualAnnotationTokens()}
          <Typeahead
            ref="tags"
            maxVisible={5}
            options={options}
            placeholder="Enter tags here..."
            onKeyDown={this.handleKeyPress}
            onOptionSelected={this.onOptionSelected}
          />
        </div>
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    learners: state.report.get('learners').toJS(),
  }
};

export default connect(mapStateToProps)(TagTools);
