const jsdiff = require('diff');


// Define custom diff object (use base diff implementation, but override some methods)
const customWordDiff = new jsdiff.Diff();

// Consider indent-level and numbering markers as separate tokens along with usual words
const customTokenSplitRegExp = /(__\/ILVL\/\d+?\/__|__\/NBR\/.+?\/__)/;
const normalTokenSplit = /(\s+|[^\w\s]+)/;

customWordDiff.tokenize = (value) => {
    // Filter out empty tokens
    if (value.match(customTokenSplitRegExp)) {
        return value.split(customTokenSplitRegExp).filter(Boolean);
    } else {
        return value.split(normalTokenSplit);
    }
};

customWordDiff.equals = (left, right) => {
    // Ignore leading/trailing spaces
    return left.trim() === right.trim();
};


module.exports = customWordDiff;
