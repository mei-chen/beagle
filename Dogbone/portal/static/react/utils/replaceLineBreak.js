var LINEBREAK_MARKER = require('./LINEBREAK_MARKER');

/**
 * replaceLineBreakMarker
 *
 * @param {string} string string to replace line break marker
 * @param {?string} replaceString the string to replace the line break marker
 * with. Default: '\n' [new line]
 */
function replaceLineBreakMarker(str, replaceString) {
  var newString = replaceString || '\n';
  return str.replace(new RegExp(LINEBREAK_MARKER, 'g'), newString);
}


module.exports = replaceLineBreakMarker;
