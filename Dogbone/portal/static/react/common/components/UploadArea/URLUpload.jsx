/* NPM Modules */
var React = require('react');

/* Style */
require('./styles/URLUpload.scss');

var URLUpload = React.createClass({

  onURLInput(e) {
    let fileName = e.target.value;
    let url = e.target.value;
    console.log('URL: ', e.target.value);

    this.props.setFileState({
      fileName: fileName,
      source: 'url',
      fileUrl: url,
      showUploadButton: true,
    });
  },

  render() {
    return (
      <div className="option url">
        <i className="fa fa-globe fa-3x"/>
          <div className="url-input-container">
            <input ref="urlInput" type="text" placeholder="Enter Document URL" onChange={this.onURLInput}/>
          </div>
      </div>
    );
  }
});

module.exports = URLUpload;
