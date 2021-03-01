/**
 * recursivelyInsertLineBreaks
 *
 * @author glifchits
 *
 */
import _ from 'lodash';

var React = require('react');
var invariant = require('invariant');

// @iuliux's predefined line break marker
var BR = require('./LINEBREAK_MARKER');


/**
 * splitStringIntoSpans
 *
 * Given just a string, try to split the string using the linebreak marker.
 * If there is a linebreak, returns
 *  [<span>line 1</span> <br /> <span>line 2</span>]
 *
 * Otherwise, returns just the original string.
 *
 * @param {string} theString string to split
 * @param {?object} style inline styles to apply to the span
 */
function splitStringIntoSpans(theString, style) {
  style = style || {};
  invariant(
    typeof theString === 'string',
    `splitStringIntoSpans received non-string type ${typeof theString}`
  );

  var split = theString.split(BR);
  // no splitting to be done.
  if (split.length === 1) {
    // just return the string
    return (
      <span style={style}>{theString}</span>
    );
  }

  // there is splitting to be handled
  var children = [];
  split.forEach((splitSubstring, idx) => {
    if (splitSubstring !== '') {
      children.push(<span key={`${idx}.span`} style={style}>{splitSubstring}</span>);
    }
    children.push(<br key={`${idx}.br`} />);
  });
  return _.flatten(_.dropRight(children));
}


/**
 * insertLineBreaks
 *
 * Consumes a React child and splits the text contents if there are linebreaks.
 * A child should be a ReactElement <span> or just a string.
 *
 * If the element does not contain linebreaks, return the element.
 * If the element does contain linebreaks, returns
 *   [<span> <br> <span>]
 *
 * @param {ReactElement|string} sentencePart a <span> or a string
 * @returns {array:ReactElement|string}
 */
function insertLineBreaks(sentencePart) {
  if (typeof sentencePart === 'string') {
    return splitStringIntoSpans(sentencePart);

  } else if (
    React.isValidElement(sentencePart) &&
    sentencePart.type === 'span'
  ) {
    var { children, style } = sentencePart.props;
    // `children` is a plain text node, i.e. a string
    return splitStringIntoSpans(children, style);

  } else if (
    React.isValidElement(sentencePart) &&
    sentencePart.type === 'br'
  ) {
    return sentencePart;

  } else {
    console.error('not sure how to handle sentencePart', sentencePart);
    return sentencePart;
  }
}


module.exports = insertLineBreaks;
