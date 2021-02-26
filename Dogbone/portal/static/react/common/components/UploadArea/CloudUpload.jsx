/* NPM Modules */
import React from 'react';

/* Style */
require('./styles/CloudUpload.scss');

const CloudUpload = React.createClass({

  propTypes: {
    setFileState : React.PropTypes.func.isRequired
  },

  handleDropboxFile() {
    var self = this;

    /* Define Dropbox options */
    var dropboxOptions = {
      // Required. Called when a user selects an item in the Chooser.
      success(files) {
        var f = files[0];
        self.props.setFileState({
          fileName: f.name,
          source: 'dropbox',
          fileUrl: f.link,
          showUploadButton: true,
        });
      },

      // Optional. Called when the user closes the dialog without selecting a file
      // and does not include any parameters.
      cancel() {},

      // Optional. "preview" (default) is a preview link to the document for sharing,
      // "direct" is an expiring link to download the contents of the file. For more
      // information about link types, see Link types below.
      linkType: 'direct', // or "preview"

      // Optional. A value of false (default) limits selection to a single file, while
      // true enables multiple file selection.
      multiselect: false, // or true

      // Optional. This is a list of file extensions. If specified, the user will
      // only be able to select files with these extensions. You may also specify
      // file types, such as "video" or "images" in the list. For more information,
      // see File types below. By default, all extensions are allowed.
      extensions: ['.pdf', '.docx', '.txt', '.doc'],
    };

    window.Dropbox.choose(dropboxOptions);
  },


  handleGoogleFile() {
    var self = this;
    var setGoogleFileState = function(fileName, fileURL, accessToken, source) {
      self.props.setFileState({
        fileName: fileName,
        fileUrl: fileURL,
        source: source,
        accessToken: accessToken,
        showUploadButton : true
      });
    };
    window.openPicker(setGoogleFileState);
  },

  render() {
    return (
      <div className="option cloud-upload">
        <div className="upload-app" onClick={this.handleGoogleFile}>
          <i className="fab fa-google-drive fa-3x" />
          <div className="upload-app-text">
            <span>Google Drive</span>
          </div>
        </div>
        <div className="upload-app" onClick={this.handleDropboxFile}>
          <i className="fab fa-dropbox fa-3x" />
          <div className="upload-app-text">
            <span>Dropbox</span>
          </div>
        </div>
      </div>
    );
  }
});

module.exports = CloudUpload;
