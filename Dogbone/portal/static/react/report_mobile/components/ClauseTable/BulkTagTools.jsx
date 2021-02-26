/* NPM Modules */
import _ from 'lodash';
var React = require('react');
var log = require('utils/logging');
var Tokenizer = require('react-typeahead').Tokenizer;

/* Utilities */
var intersectionArrayOfObjects = require('utils/intersectionArrayOfObjects');

/* Stores & Actions */
var { ReportActions } = require('report/actions');

/* Constants */
require('utils/constants.js');

/* Style */
const styles = require('./styles/BulkTagTools.scss');

var BulkTagTools = React.createClass({

  propTypes: {
    user: React.PropTypes.object.isRequired,
    sentences: React.PropTypes.array.isRequired,
  },

  /*
   * lightwieght compare function to use in the intersectionArrayOfObjects
   * function. Used to find common tags in the bulk tag tools.
   */
  compareObjects(a,b) {
    //first check to see if the attributes exist
    if ( !(a.label === undefined) && !(b.label === undefined) && !(a.approved === undefined) && !(b.approved === undefined)) {
      return (a.label === b.label && a.approved === b.approved)
    } else {
      return false }
  },


  getCommonAnnotations() {
    const { sentences } = this.props;
    const sentenceAnnotations = sentences.map(s => {
      //see if the sentence has any annotations, if so map the objects to an array. if not, empty list
      const annotations = !!s.annotations ? s.annotations : [];
      return annotations;
    });
    // initialize common annotations as first sentence annotations list
    let commonAnnotations = sentenceAnnotations[0];
    // for the rest of the sentence tags... `slice(1)`
    sentenceAnnotations.slice(1).forEach(currentSentenceAnnotationsList => {
      //console.log("sentenceAnnotationCurrent: ", currentSentenceAnnotationsList);
      // repeatedly take intersection of each tags list
      commonAnnotations = intersectionArrayOfObjects(commonAnnotations, currentSentenceAnnotationsList, this.compareObjects);
    });
    return commonAnnotations;
  },

  generateDefaultSelected() {
    var common = this.getCommonAnnotations();
    var defaults = common.map( (a, key) => {
      return {
        name: a.label.toLowerCase(),
        perm: false,
        class: a.type,
        suggested: (!a.approved && a.type === SUGGESTED_TAG_TYPE)
      };
    });
    return defaults;
  },

  onDuplicateAdd() {
    console.log("DUPLICATE ADD");
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
      log.error(`Requested bulk tag delete for tag: "${token}" failed. Unable to find "${token}" in annotations object`);
      return
    }
    return annotation
  },

  // Add bulk sentences only requires a string because you can only add manual tokens which needs no type/sublabel/party on the backend
  addBulkSentenceTag(token) {
    var sentenceIdxs = _.pluck(this.props.sentences, 'idx');
    const annotation = {};
    //build the new annotation object to bulk create
    annotation['type'] = MANUAL_TAG_TYPE;
    annotation['label'] = token;

    ReportActions.addBulkTags(sentenceIdxs, [annotation]);
  },

  approveBulkSentenceTag(token) {
    var sentenceIdxs = _.pluck(this.props.sentences, 'idx');
    const annotation = this.findAnnotation(token);

    ReportActions.approveBulkTags(sentenceIdxs, [annotation]);
  },

  deleteBulkSentenceTag(token) {
    var sentenceIdxs = _.pluck(this.props.sentences, 'idx');
    const annotation = this.findAnnotation(token);
    ReportActions.deleteBulkTags(sentenceIdxs, [annotation]);
  },

  onTokenAdd(token) {
    log("onBulkTokenAdd: ", token);
    this.addBulkSentenceTag(token);
  },

  onTokenRemove(token) {
    log("onBulkTokenRemove: ", token);
    this.deleteBulkSentenceTag(token);
  },

  onTokenApprove(token) {
    console.log("APPROVE: ", token);
    log("onBulkTokenSuggestedTagApprove");
    this.approveBulkSentenceTag(token);
  },

  onTokenDisapprove(token) {
    console.log("DISAPPROVE: ", token);
    log("onBulkTokenSuggestedTagDisapprove");
    this.deleteBulkSentenceTag(token);
  },

  render() {
    const defaultSelected = this.generateDefaultSelected();
    const options = this.props.user.tags || [];
    const defaultSelectedHash = defaultSelected.map(d => (d.suggested + d.name + d.class)).join('');
    return (
      <div className={styles.tagTools}>
        <Tokenizer
          key={defaultSelectedHash}
          options={options}
          placeholder="Enter bulk tags here..."
          defaultSelected={defaultSelected}
          onTokenAdd={this.onTokenAdd}
          onTokenRemove={this.onTokenRemove}
          onDuplicateAdd={this.onDuplicateAdd}
          onTokenApprove={this.onTokenApprove}
          onTokenDisapprove={this.onTokenDisapprove}
        />
      </div>
    );
  }
});


module.exports = BulkTagTools;
