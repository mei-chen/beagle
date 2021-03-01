import _ from 'lodash';

/**
 * logFormat
 *
 * @param {any} arguments just pass in things that you want to log
 * @returns {array} things which are to be console logged
 */
function logFormat() {
  return [`(${__ENV__})`, ...arguments];
}


function log() {
  if (typeof console === 'object' && typeof console.log === 'function') {
    console.log(...logFormat(...arguments));
  }
}


for (let method of ['log', 'debug', 'warn', 'info', 'error']) {
  const logMethod = function() {
    if (typeof console === 'object' && typeof console[method] === 'function') {
      console[method](...logFormat(...arguments));
    }
  };
  log[method] = logMethod;
}


const oldOnError = window.onerror;
window.onerror = function(msg, url, line, col) {
  log.error(`Error: ${msg} at ${url} on ${line}:${col}`);
  if (oldOnError != null) {
    oldOnError(...arguments);
  }
};


module.exports = log;
