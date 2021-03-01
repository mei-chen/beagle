var LINEBREAK_MARKER = require('./LINEBREAK_MARKER');


/**
 * replaceWithLineBreakMarker
 *
 * @param {string} str string which will be replaced with line break marker
 * @param {?string} replaceString string which will be replaced with the line
 * break marker (Default: '\n')
 */
function replaceWithLineBreakMarker(str, replaceString) {
  var oldString = replaceString || '\n';
  return str.replace(new RegExp(oldString, 'g'), LINEBREAK_MARKER);
}


module.exports = replaceWithLineBreakMarker;
