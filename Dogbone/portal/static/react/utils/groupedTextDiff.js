/*
 * groupedTextDiff
 *
 * Import:
 *  var groupedTextDiff = require('utils/groupedTextDiff');
 *
 * This makes a word by word diff between two texts and groups them by
 * contiguous chunks.
 *
 */

const customWordDiff = require('./customWordDiff');
const replaceLineBreaks = require('./replaceLineBreak');


// See richtext.xmldiff.simply_diff for more details
const simplifyDiff = function(diff) {
  const diffSimplified = [];

  const isEqualSpace = function(diffEntry) {
    return !diffEntry.removed && !diffEntry.added && !diffEntry.value.trim();
  }

  const n = diff.length;
  let i = 0, offset;
  let removed, added, equal;
  while (i < n) {

    if (diff[i].removed) {
      removed = Object.assign({}, diff[i]);
      if (i + 1 < n && diff[i + 1].added) {
        added = Object.assign({}, diff[i + 1]);
        i += 2;
      } else {
        diffSimplified.push(removed);
        i++;
        continue;
      }

      while (i < n && isEqualSpace(diff[i])) {
        offset = 1;
        removed.value += diff[i].value;
        added.value += diff[i].value;
        if (i + 1 < n && diff[i + 1].removed) {
          removed.value += diff[i + 1].value;
          offset = 2;
          if (i + 2 < n && diff[i + 2].added) {
            added.value += diff[i + 2].value;
            offset = 3;
          }
        }
        i += offset;
      }

      diffSimplified.push(removed);
      diffSimplified.push(added);

    } else if (diff[i].added) {
      added = Object.assign({}, diff[i]);
      diffSimplified.push(added);
      i++;

    } else {
      equal = Object.assign({}, diff[i]);
      diffSimplified.push(equal);
      i++;
    }
  }

  return diffSimplified;
};

const addSpaceAfterMarker = (text) => {
  return text.replace(/\/__/g, '/__ ');
};

export default (oldText, newText) => {
  oldText = replaceLineBreaks(addSpaceAfterMarker(oldText), '\n').trim();
  newText = replaceLineBreaks(addSpaceAfterMarker(newText), '\n').trim();
  const diff = customWordDiff.diff(oldText, newText);
  return simplifyDiff(diff);
};
