var Reflux = require('reflux');
var $ = require('jquery');


var InitialSampleDocsStore = Reflux.createStore({
  /**
   * init
   *
   * Method called when this store is created for the first time.  Reflux Stores
   * are singletons, so this is called only once per browser page load.
   *
   */
  init() {
    this.getFromServer();
  },

  issueNotification(data) {
    this.data = data;
    this.trigger(data);
  },

  getFromServer() {
    $.get('/api/v1/user/me/initial_sample_docs', resp => {
      this.issueNotification(resp.samples);
    });
  },

});


module.exports = InitialSampleDocsStore;
