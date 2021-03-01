/**
 * LockActions
 *
 * Actions for dealing with locks
 */
var Reflux = require('reflux');


var LockActions = Reflux.createActions({
  requestLock: { children: ['acquired', 'failed'] },
  releaseLock: { asyncResult: true },
  queryLock: { asyncResult: true }
});


module.exports = LockActions;
