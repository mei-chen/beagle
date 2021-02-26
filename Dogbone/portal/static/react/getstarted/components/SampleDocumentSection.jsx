var React = require('react');
var Reflux = require('reflux');
require('./styles/SampleDocumentSection.scss');   //stylings for component

var InitialSampleDocsStore = require('../stores/InitialSampleDocsStore');


var SampleDocument = React.createClass({

  propTypes: {
    subtitle: React.PropTypes.string
  },

  onDocClick() {
    let url = `/report/${this.props.docuuid}`;
    window.location = url;
  },

  render() {
    return (
      <div className="sample-document" onClick={this.onDocClick}>
        <div className="icon">
          <i className="fa fa-file-alt fa-4x" />
        </div>
        <div className="subtitle">
          {this.props.subtitle}
        </div>
      </div>
    );
  }

});

var SampleDocumentSection = React.createClass({

  mixins: [Reflux.connect(InitialSampleDocsStore, 'initdocs')],

  render() {
    if (this.state.initdocs) {
      var docs = this.state.initdocs.map(item => {
        let title = item[0];
        let uuid = item[1];
        return (<SampleDocument subtitle={title} docuuid={uuid}/>);
      });
    } else {
      docs = (
        <div className="loading">
          <i className="fa fa-cog fa-spin fa-3x" />
          <div className="loading-text">Loading Documents</div>
        </div>
        );
    }
    return (
      <div className="sample-document-section">
        <div className="explanation">
          Use one of our sample documents
        </div>
        <div className="documents">
          {docs}
        </div>
      </div>
    );
  }

});

module.exports = SampleDocumentSection;