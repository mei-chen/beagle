/**
 * splitExternalReferences
 *
 * Splits a sentence into an array of objects that specify how the sentence is
 * broken down into its components being marked as external references.
 *
 * @param {object} sentence contains external references
 * @return {array} array of objects. Each object looks like:
 *  { text: {string}, ref: {bool} }
 */
import _ from 'lodash';

module.exports = function(sentence) {
  var text = sentence.form;
  var references = sentence.external_refs;
  var refs = _.sortBy(references, 'offset');
  var strings = [];
  var index = 0;

  refs.forEach(ref => {
    var refStartIndex = ref.offset;
    strings.push({
      text: text.slice(index, refStartIndex),
      ref: false
    });
    strings.push({
      text: ref.form,
      ref: true
    });
    index = ref.offset + ref.length;
  });
  strings.push({
    text: text.slice(index), // to end of string
    ref: false
  });

  return strings;
};
