import _ from 'lodash';

var React = require('react');
var invariant = require('invariant');

// @iuliux's predefined indent-level and numbering markers
const ILVL_MARKER = require('./INDENTLEVEL_MARKER');
const NBR_MARKER = require('./NUMBERING_MARKER');


/**
 * splitStringIntoSpans
 *
 * See insertLineBreaks.jsx
 */
export const splitStringIntoSpans = (theString, style) => {
  style = style || {};
  invariant(
    typeof theString === 'string',
    `splitStringIntoSpans received non-string type ${typeof theString}`
  );

  const ilvlRegExp = new RegExp(ILVL_MARKER);
  const nbrRegExp = new RegExp(NBR_MARKER);
  const split = theString.split(ilvlRegExp);

  // no splitting to be done.
  if (split.length === 1) {
    // just return the string
    return (
      <span style={style}>{theString.replace(nbrRegExp, '$1 ')}</span>
    );
  }

  // there is splitting to be handled
  const children = [];
  split.forEach((splitSubstring, idx) => {
    if (idx % 2 == 0) {
      // Odd indices are the separators
      if (splitSubstring !== '') {
        var ilvl = 0;
        if (idx > 0) {
          ilvl = parseInt(split[idx-1]);
        }
        const combinedStyle = _.extend({}, style, {paddingLeft: ilvl * 30 + 'px'});
        const nbrSplitSubstring = splitSubstring.replace(nbrRegExp, '$1 ');
        children.push(<span key={`${idx}.span`} style={combinedStyle}>{nbrSplitSubstring}</span>);
      }
    }
  });
  return _.flatten(children);
}


/**
 * insertIndents
 *
 * See insertLineBreaks.jsx
 */
const insertIndents = (sentencePart) => {
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


export default insertIndents;
