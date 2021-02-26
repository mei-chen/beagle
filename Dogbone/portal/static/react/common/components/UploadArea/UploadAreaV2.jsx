/**********************************************
* UploadArea
*
* This is a re-usable components that offers 4
* different methods of upload.
*
* 1) Standard Local FilePicker
* 2) Drag and Drop
* 3) Cloud Upload (Gdrive and Dropbox)
* 4) Plaintext Paste
*
* Whatever the component has as children will be used as the default
* markup before a document is uploaded
*
* NOTE: Be sure to include the follwing header scripts in any template that
* uses this component
*
*   <!--Dropbox Include-->
*   <script type="text/javascript" src="https://www.dropbox.com/static/api/2/dropins.js" id="dropboxjs" data-app-key="tsx9rcah18qz3c7"></script>
*   <!--Google Include-->
*   <script src="https://www.google.com/jsapi?key=AIzaSyAb_m3H2ckI6r69wqbUtGjJhkBpjEzBY3o"></script>
*   {% include "gdrive.html" %}
*   <script type="text/javascript" src="https://apis.google.com/js/client.js?onload=onApiLoad"></script>
*
************************************************/


/* NPM Modules */
import React from 'react';
import log from 'utils/logging';
import $ from 'jquery';

/* Components */
import FeedBackRow from './FeedBackRow';
import CloudUpload from './CloudUpload';
import DragAndDrop from './DragAndDrop';
import LocalFile from './LocalFile';
import URLUpload from './URLUpload';
import { Notification } from 'common/redux/modules/transientnotification';

/* Style */
require('./styles/UploadAreaV2.scss');


const UploadAreaV2 = React.createClass({

  getInitialState() {
    return {
      showUploadButton: false,
      fileName: null,
      fileData: null,
      fileList: null,
      fileUrl: null,
      source: null,
      accessToken: null,
      preSniff: true,
      upload: null,
      conversion: null,
      docUUID: null,
    };
  },

  /**
  * postURLUpload()
  *
  * This makes use of the URL upload API endpoint at
  * /api/v1/document/upload
  *
  */
  postURLUpload() {
    const url = '/api/v1/document/upload';
    const data = JSON.stringify({ url : this.state.fileUrl });

    $.ajax({
      url: url,
      method: 'POST',
      data: data,
      dataType: 'json',
    })
    .done(resp => {
      const docUUID = resp.uuid;
      //communicate to the feedback row that the upload has started
      this.refs.FeedBackRow.setState({
        docUUID: docUUID
      });
    })
    .fail(resp => {
      log.error('request error', resp);
      Notification.error('Invalid URL, please enter a URL path to a .txt, .docx, .doc or a .pdf');
    });
  },

  /**
  * postFileUpload()
  *
  * This makes use of the regular upload enpoint
  * at /upload
  *
  */
  postFileUpload(formURL, formData) {
     // thanks https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects#Sending_files_using_a_FormData_object
    $.ajax({
      url: formURL,
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false
    })
    .done(resp => {
      const docUUID = resp.document.uuid;
      //communicate to the feedback row that the upload has started
      this.refs.FeedBackRow.setState({
        docUUID: docUUID
      });
    })
    .fail(resp => {
      log.error('request error', resp);
    });
  },

  /**
   * onClickUploadFile
   *
   * What the app does when the user clicks "Sniff"
   *
   * Thanks to
   * https://github.com/ambitioninc/react-ui/blob/5e187329508856d07de4153579ae29d294b8bcdb/src/ajax-form/components/utils.js
   * for the AJAX react form handling
   *
   */
  onClickUploadFile() {
    var uploadForm = this.refs.uploadForm.getDOMNode();
    var formURL = uploadForm.action;
    var formData = new FormData(uploadForm);

    // append the data from the fileList to the form's file field.
    if (this.state.fileList !== null) {
      formData.append('file', this.state.fileList[0]);
    }


    //remove the upload button
    this.setState({
      showUploadButton : false
    });
    //show the uploading text
    this.refs.FeedBackRow.setState({
      upload: 'started'
    });

    // Select the proper upload endpoint
    if (this.state.source === 'url') {
      console.log('URL UPLOAD: ', this.state.source);
      this.postURLUpload();
    } else {
      this.postFileUpload(formURL, formData);
    }
  },

  /**
  * cancelDocument()
  *
  * clear the state and delete the input value should the user change their
  * mind an want to upload a different document
  */
  cancelDocument() {
    this.setState({
      showUploadButton: false,
      fileName: null,
      fileData: null,
      fileList: null,
      fileUrl: null,
      source: null,
      accessToken: null,
      docUUID: null,
    });
    //clear the file input so the onChange listener works
    this.refs.fileInput.getDOMNode().value = null;
    this.refs.URLUpload.refs.urlInput.getDOMNode().value = null;
  },

  /**
  * setFileState
  *
  * Passed down to the various upload method children to allow
  * them to set the state of UploadArea (functionally filling out
  * the upload form)
  *
  */
  setFileState(state) {
    this.setState(state);
  },

  /**
  * onLocalClick()
  *
  * Onclick listener that will artifically click the hidden form input
  */
  onLocalClick() {
    this.refs.fileInput.getDOMNode().click();
  },

  /**
  * onLocalFileSelect(e)
  *
  * Listens for changes to the file input form field, confirms
  * a file was indeed selected, then sets the states accordingly
  */
  onLocalFileSelect(e) {
    e.preventDefault();
    var fileList = e.target.files;
    var title = fileList[0].name;

    if (fileList) {
      this.setState({
        showUploadButton : true,
        fileName : title,
        source : 'local'
      });
    }
  },

  /**
  * onLocalFileDrop(e)
  *
  * Passed to the dropzone component and
  * recieves the onDrop event
  */
  onLocalFileDrop(e) {
    e.preventDefault();
    var fileList = e.dataTransfer.files;
    var title = fileList[0].name;

    if (fileList) {
      this.setState({
        showUploadButton : true,
        fileName : title,
        fileList : fileList,
        source : 'local'
      });
    }
  },


  render() {
    var uploadForm = (
      <form style={{ display: 'none' }} ref="uploadForm" encType="multipart/form-data" action="/upload" method="POST">
        <input ref="fileInput" type="file" id="file" name="file" onChange={this.onLocalFileSelect}/>
        <input type="text" value={this.state.fileName} id="file_name" name="file_name"/>
        <input type="text" value={this.state.fileData} id="filedata" name="filedata"/>
        <input type="text" value={this.state.fileUrl} id="fileurl" name="fileurl"/>
        <input type="text" value={this.state.source} id="filesource" name="filesource"/>
        <input type="text" value={this.state.accessToken} id="accessToken" name="accessToken"/>
      </form>
    );

    //style={{ display: 'none' }}

    return (
        <div className="upload-area">
          <span className="explanation">Upload a legal document</span>
          {uploadForm}
          <div className="row">
            <LocalFile
              onLocalClick={this.onLocalClick} />
            <DragAndDrop
              ref="DragAndDrop"
              onLocalFileDrop={this.onLocalFileDrop}/>
          </div>
          <div className="row">
            <URLUpload ref="URLUpload"
              setFileState={this.setFileState}/>
            <CloudUpload
              setFileState={this.setFileState} />
          </div>
          <FeedBackRow ref="FeedBackRow"
            enabled={this.state.showUploadButton}
            onClickUploadFile={this.onClickUploadFile}
            cancelDocument={this.cancelDocument}
            documentTitle={this.state.fileName}
            children={this.props.children}/>
        </div>
    );
  }

});

module.exports = UploadAreaV2;
