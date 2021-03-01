import React from 'react';
import ReactDOM from 'react-dom';
import { connect } from 'react-redux';
import $ from 'jquery';
import io from 'socket.io-client';

//Actions
import { checkForAnalyzed, sendZipPasswords } from '../redux/modules/upload';

// App
import log from 'utils/logging';
import { Notification } from 'common/redux/modules/transientnotification';
import Dropzone from './Dropzone';
import ZipPassword from './ZipPassword';
import SummaryPage from './SummaryPage';
import ProgressIcon from './ProgressIcon';

require('./styles/Upload.scss');   //stylings for component

/* global Dropbox, openPicker */

const socket = io(window.socketServerAddr);

const UploadApps = React.createClass({

  propTypes: {
    handleDropbox: React.PropTypes.func.isRequired,
    handleGoogle: React.PropTypes.func.isRequired
  },

  getInitialState() {
    return {}
  },

  componentDidUpdate() {
    window.Intercom('update');
  },

  render() {
    return (
      <div className="upload-row">
        <div onClick={this.props.handleGoogle} id="gdrive" className="upload-tool-btn">
          <a className="upload-iconText" id="pick" href="#">
            <i className="fab fa-google-drive fa-4x" />
          </a>
        </div>
        <div onClick={this.props.handleDropbox} id="dropbox" className="upload-tool-btn">
          <a className="upload-iconText" href="#">
            <i className="fab fa-dropbox fa-4x" />
          </a>
        </div>
      </div>
    );
  }

});


var DropzoneArea = React.createClass({

  propTypes: {
    enabled: React.PropTypes.bool.isRequired,
    handleReceivedFiles: React.PropTypes.func,
    fileName: React.PropTypes.string,
    filesCount: React.PropTypes.number
  },

  render() {
    var fileSelectedText = 'Upload a .txt, .docx, .doc, .pdf, .xml or .zip';

    var dropzoneStyle = {
      width: 'inherit',
      height: 100
    };

    if (!this.props.totalFilesToUpload) {
      fileSelectedText = 'Upload a .txt, .docx, .doc, .pdf, .xml or .zip';
    }
    else if (this.props.totalFilesToUpload === 1) {
      fileSelectedText = this.props.fileName;
    }
    else if (this.props.totalFilesToUpload > 1) {
      fileSelectedText = `selected ${this.props.totalFilesToUpload} files`;
    }

    return (
      <div className="beagle-dragndrop">
        <Dropzone enabled={this.props.enabled} ref="dropzone" onDrop={this.props.handleReceivedFiles} style={dropzoneStyle}>
          <div id="chooseFile" className="upload-tool-btn">Select file from computer</div>
          <div id="filenameview">
            <h3 id="fileName">{fileSelectedText}</h3>
          </div>
        </Dropzone>
      </div>
    );
  }

});

const UploadAreaComponent = React.createClass({
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
      localFileList: null,
      gDriveFileList: null,
      dropboxFileList: null,
      uploadedFilesCounter: null,
      totalFilesToUpload: null,
      totalFilesConverted: null,
      askZipPassword: false,
      encryptedDocuments: null,
      zipWrongPassword: false,
      showSummaryPage: false,
      summaryList: [],
      batchId: null,
      fileNamesList: '',
      fileNamesCount: 0,
      isBatchFile: true,
      uploadId: null,
      showBatchName: false,
    };
  },

  componentDidMount() {
    this.socketListener();
  },

  socketListener() {
    const { dispatch, setting } = this.props;

    socket.on('message', msg => {
      log('msg received', msg);
      var type = msg.notif;

      if (type === 'DOCUMENT_UPLOADED') {
        const uploadedCounter = this.state.uploadedFilesCounter !== null ? this.state.uploadedFilesCounter + 1 : 1;
        this.setState({
          uploadedFilesCounter: uploadedCounter,
        });
        if (this.state.uploadedFilesCounter === this.state.totalFilesToUpload) {
          this.setState({
            upload: 'finished',
            conversion: 'started'
          });
        }
      }

      else if (type === 'DOCUMENT_CONVERTED') {
        if (this.state.totalFilesToUpload == 1) {
          setTimeout(
            () => {
              location.href = `${msg.document.report_url}${setting.get('default_report_view') || ''}`;
            }, 1500
          );
        }
        const convertedCounter = this.state.totalFilesConverted !== null ? this.state.totalFilesConverted + 1 : 1;
        this.setState({
          totalFilesConverted: convertedCounter,
        });
        if (convertedCounter === this.state.totalFilesToUpload) {
          this.setState({
            conversion: 'finished'
          });
        }
      }

      else if (type === 'BATCH_PROCESSING_COMPLETED') {
        this.setState({
          conversion: 'finished'
        });
      }

      else if (type === 'DOCUMENT_ERROR_MALFORMED') {
        dispatch(Notification.error('The document you uploaded is malformed. Please try again.'));
        this.setState({
          conversion: 'finished'
        });
        setTimeout(
          () => {
            //if not uploading batch
            if (!this.state.showSummaryPage) {
              window.location = '/upload/file';
            }
          }, 3000
        );
      }

      else if (type === 'DOCUMENT_ERROR_UNSUPPORTED_LANGUAGE') {
        dispatch(Notification.error('Only English is supported at the moment. A different language has been detected.'));
        this.setState({
          conversion: 'finished'
        });
        setTimeout(
          () => {
            //if not uploading batch
            if (!this.state.showSummaryPage) {
              window.location = '/upload/file';
            }
          }, 3000
        );
      }

      else if (type === 'DOCUMENT_ERROR_NOT_FOUND') {
        dispatch(Notification.error('We encountered an unexpected error. Please try again later.'));
        this.setState({
          conversion: 'finished'
        });
        setTimeout(
          () => {
            //if not uploading batch
            if (!this.state.showSummaryPage) {
              window.location = '/upload/file';
            }
          }, 3000
        );
      }

      else if (type === 'DOCUMENT_ERROR_FORMAT_UNSUPPORTED') {
        dispatch(Notification.error('The document file type you uploaded is currently unsupported by Beagle. Please try again with a .txt, .docx, .doc or a .pdf.'));
        this.setState({
          conversion: 'finished'
        });
        setTimeout(
          () => {
            //if not uploading batch
            if (!this.state.showSummaryPage) {
              window.location = '/upload/file';
            }
          }, 7000
        );
      }

      else if (type === 'DOCUMENT_ERROR_TOO_LARGE_TO_OCR') {
        dispatch(Notification.error('The document you uploaded is too large to be OCRed.'));
        this.setState({
          conversion: 'finished'
        });
        setTimeout(
          () => {
            //if not uploading batch
            if (!this.state.showSummaryPage) {
              window.location = '/upload/file';
            }
          }, 7000
        );
      }

      else if (type === 'BATCH_EMPTY') {
        dispatch(Notification.error('The batch you were about to upload is empty or does not contain any supported documents.'));
        this.setState({
          upload: 'finished',
          conversion: 'finished'
        });
        setTimeout(
          () => {
            //if not uploading batch
            if (!this.state.showSummaryPage) {
              window.location = '/upload/file';
            }
          }, 7000
        );
      }

      else if (type === 'EASYPDF_ERROR') {
        dispatch(Notification.error('We are sorry, there was an unexpected error with processing your PDF. The Beagle team has been alerted. Please try a different version of the document.'));
        this.setState({ conversion: 'finished' });
        setTimeout(() => {
          //if not uploading batch
          if (!this.state.showSummaryPage) {
            window.location = '/upload/file';
          }
        }, 3000);
        Intercom('trackEvent', 'easypdf-error');
      }
    });
  },

  /**
   * openInNewTab
   *
   * function changes state of dropboxFileList without mutation
   *
   * @param {string} link of new tab
   */
  openInNewTab(url) {
    var win = window.open(url, '_blank');
    win.focus();
  },

  /**
   * enableUploadButton
   *
   * function shows the sniff button
   *
   */
  enableUploadButton() {
    this.setState({ showUploadButton: true });
  },

  /**
   * disableUploadButton
   *
   * function hides the sniff button
   *
   */
  disableUploadButton() {
    this.setState({ showUploadButton: false });
  },


  /**
   * handleGoogleFile
   *
   * Stores new files in state when google drive files was picked
   *
   */
  handleGoogleFile() {
    var setGoogleFileState = (fileName, fileURL, accessToken, source) => {
      this.changeGDriveFilesState({
        fileName: fileName,
        fileUrl: fileURL,
        source: source,
        accessToken: accessToken
      });
      this.generateFilesName(fileName);
      this.incrementFilesCounter(1);
      this.enableUploadButton();
    };
    openPicker(setGoogleFileState);
    Intercom('trackUserEvent', 'upload-googledrive');
  },

  /**
   * handleDropboxFile
   *
   * Stores new files in state when dropbox files was picked
   *
   */
  handleDropboxFile() {
    /* Define Dropbox options */
    var dropboxOptions = {
      // Required. Called when a user selects an item in the Chooser.
      success: (files) => {
        files.map(file => {
          this.generateFilesName(file.name);
        });
        this.changeDropboxFilesState(files);
        this.incrementFilesCounter(files.length);
        this.enableUploadButton();
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
      multiselect: true, // or true

      // Optional. This is a list of file extensions. If specified, the user will
      // only be able to select files with these extensions. You may also specify
      // file types, such as "video" or "images" in the list. For more information,
      // see File types below. By default, all extensions are allowed.
      extensions: ['.pdf', '.docx', '.txt', '.doc', '.zip'],
    };

    Dropbox.choose(dropboxOptions);
    Intercom('trackUserEvent', 'upload-dropbox');
  },

  /**
   * changeGDriveFilesState
   *
   * function changes state of gDriveFilesState without mutation
   *
   * @param {obj} parameters of picked file that user selected from google drive
   *
   */
  changeGDriveFilesState(newFile) {
    if (this.state.gDriveFileList !== null) {
      const gDriveFilesArray = [...this.state.gDriveFileList, newFile];
      this.setState({
        gDriveFileList: gDriveFilesArray,
      });
    } else {
      this.setState({
        gDriveFileList: [newFile],
      });
    }
  },

  /**
   * changeDropboxFilesState
   *
   * function changes state of dropboxFileList without mutation
   *
   * @param {array} files the files that the user selected from
   * the dropbox
   */
  changeDropboxFilesState(newFiles) {
    if (this.state.dropboxFileList !== null) {
      this.setState({
        dropboxFileList: [...this.state.dropboxFileList, ...newFiles]
      });
    } else {
      this.setState({
        dropboxFileList: newFiles,
      });
    }
  },

  /**
   * changeLocalFilesState
   *
   * function changes state of localFileList without mutation
   *
   * @param {array} files the files that the user dropped onto, or selected from
   * the drop zone
   */
  changeLocalFilesState(newFiles) {
    if (this.state.localFileList !== null) {
      this.setState({
        localFileList: [...this.state.localFileList, ...newFiles]
      });
    } else {
      this.setState({
        localFileList: newFiles,
      });
    }
  },

  /**
   * incrementFilesCounter
   *
   * Increments totalFilesToUpload state when new files droped/picked
   *
   * @param {int} number of files to increment
   */
  incrementFilesCounter(index) {
    const newCounter = this.state.totalFilesToUpload !== null ? this.state.totalFilesToUpload + index : index;
    this.setState({
      totalFilesToUpload: newCounter,
    })
  },


  /**
   * generateFilesName
   *
   * Function generate's a text of files which was added/droped
   *
   * @param {string} name of file
   */
  generateFilesName(name) {
    const count = this.state.fileNamesCount + 1;
    const names = this.state.fileNamesList.length ? `${this.state.fileNamesList}, ${name}` : name;
    this.setState({
      fileNamesList: names,
      fileNamesCount: count
    })
  },

  /**
   * handleReceivedFiles
   *
   * What the dropzone does when it receives files.
   *
   * @param {array} files the files that the user dropped onto, or selected from
   * the drop zone
   */
  handleReceivedFiles(fileList) {
    if (fileList.length === 1) {
      this.generateFilesName(fileList[0].name);
    }
    const tempArray = [];
    for (const key of Object.keys(fileList)) {
      tempArray.push(fileList[key]);
    }
    this.changeLocalFilesState(tempArray);
    this.incrementFilesCounter(tempArray.length);
    this.enableUploadButton();
  },

  /**
   * uploadLocalFiles
   *
   * Function uploads each file that was picked/dropped from the computer
   */
  uploadLocalFiles() {
    if (this.state.localFileList !== null) {
      this.state.localFileList.map((fileList) => {
        this.sendLocalFileToServer(fileList);
      });
    } else {
      return true;
    }
  },

  /**
   * uploadGDriveFiles
   *
   * Function uploads each file that was picked from google-drive picker
   */
  uploadGDriveFiles() {
    if (this.state.gDriveFileList !== null) {
      this.state.gDriveFileList.map((fileList) => {
        this.sendGDriveFileToServer(fileList);
      });
    } else {
      return true;
    }
  },

  /**
   * uploadDropboxFiles
   *
   * Function uploads each file that was picked from dropbox picker
   */
  uploadDropboxFiles() {
    if (this.state.dropboxFileList !== null) {
      this.state.dropboxFileList.map((fileList) => {
        this.sendDropboxFileToServer(fileList);
      });
    } else {
      return true;
    }
  },

  /**
   * prepareDataToSend
   *
   * This function append's files info from state to formData
   *
   *
   */
  prepareDataToSend(nameOfBatch = false) {
    const uploadForm = ReactDOM.findDOMNode(this.refs.uploadForm);
    const formURL = uploadForm.action;
    const formData = new FormData();
    var data = {};
    var index = 0;

    this.disableUploadButton();
    this.onSubmitFile();

    if (this.state.localFileList !== null) {
      this.state.localFileList.map((fileList) => {
        data[`${index}`] = {
          file_name: fileList.name,
          filesource: 'local',
          fileurl: '',
          accessToken: '',
        }
        formData.append(`${index}`, fileList);
        index++
      });
    }
    if (this.state.gDriveFileList !== null) {
      this.state.gDriveFileList.map((fileList) => {
        data[`${index}`] = {
          file_name: fileList.fileName,
          filesource: fileList.source,
          fileurl: fileList.fileUrl,
          accessToken: fileList.accessToken
        }
        formData.append(`${index}`, fileList);
        index++
      });
    }
    if (this.state.dropboxFileList !== null) {
      this.state.dropboxFileList.map((fileList) => {
        data[`${index}`] = {
          file_name: fileList.name,
          filesource: 'url',
          fileurl: fileList.link,
          accessToken: ''
        }
        formData.append(`${index}`, fileList);
        index++
      });
    }
    data = JSON.stringify(data);
    nameOfBatch ? formData.append('batch_name', nameOfBatch) : null;
    formData.append('info', data);
    this.setState({
      fileNamesCount: index,
    });

    this.sendFiles(formURL, formData);
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
    if (this.state.totalFilesToUpload > 1) {
      this.openBatchNameModal();
    } else {
      this.prepareDataToSend();
    }
  },

  /**
   * sendFiles
   *
   * After all files was appended in formData, function makes request
   * to server using $.ajax
   * @param {formData} all files in form data
   * @param {string} request url
   */
  sendFiles(formURL, formData) {
    const { dispatch } = this.props;
    $.ajax({
      url: formURL,
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false
    })
    .done(resp => {
      // data already comes in JSON
      if (resp.e_archives_in_upload) {
        this.setState({
          askZipPassword: true,
          encryptedDocuments: resp.encrypted_archives,
          uploadId: resp.upload_id,
          showBatchName:false
        })
      }

      else if (resp.documents.length > 1) {
        this.setState({
          showSummaryPage: true,
          batchId: resp.upload_id,
          showBatchName:false,
          showZipPassword:false
        });
        this.checkAnalyzedDocs();
      }
    })
    .fail(resp => {
      log.error('request error', resp);
      dispatch(Notification.error('An error occured. Looks like something went wrong on our side.'));
    });
  },

  /**
   * onSubmitFile
   *
   * All the stuff that happens *after* the user clicks "sniff" and the file
   * data was sent to the server.
   *
   */
  onSubmitFile() {
    this.setState({
      preSniff: false,
      upload: 'started',
      conversion: null,
      uploadedFilesCounter: 0,
      totalFilesConverted: 0,
    });
  },

  /**
   * onSubmitZipPassword
   *
   * Send request with zip password if document encrypted
   *
   * @param {string} submitted password of zip
   */
  onSubmitZipPassword(password) {
    const { dispatch } = this.props;

    dispatch(sendZipPasswords(password, this.state.uploadId))
      .then(response => {
        response = response.data;
        if (response.e_archives_in_upload) {
          this.setState({
            zipWrongPassword: true,
            encryptedDocuments: response.encrypted_archives,
          })
        } else {
          if (response.documents.length > 1) {
            this.setState({
              showSummaryPage: true,
              zipWrongPassword: false,
              askZipPassword: false,
              batchId: response.upload_id
            });
            this.checkAnalyzedDocs();
          }
        }
      })
  },

  /**
   * cancelSubmitingZipPassword
   *
   * Close modal window with zip password field
   *
   */
  cancelSubmitingZipPassword() {
    this.enableUploadButton();
    this.setState({
      askZipPassword: false,
      preSniff: true,
      upload: null,
      conversion: null,
      uploadedFilesCounter: 0,
      totalFilesConverted: 0,
    })
  },

  /**
   * checkAnalyzedDocs
   *
   * send request to server check if documents analyzed
   *
   */
  checkAnalyzedDocs() {
    const { dispatch } = this.props;
    if (this.state.batchId) {
      dispatch(checkForAnalyzed(this.state.batchId))
        .then(response => {
          this.setState({
            summaryList: response.data.documents,
          });
        });
    }
  },

  closeSummaryPage() {
    this.setState({
      showSummaryPage: false,
    })
  },

  openBatchNameModal() {
    this.setState({
      showBatchName: true,
      showUploadButton:false,
      preSniff: false
    });
  },

  closeBatchName() {
    this.setState({
      showBatchName: false,
      askZipPassword: false,
      showSummaryPage: false,
      preSniff: true,
      upload: null,
      conversion: null,
      uploadedFilesCounter: 0,
      totalFilesConverted: 0,
    });
    this.enableUploadButton();
  },

  submitBatchName(name) {
    this.prepareDataToSend(name);
  },

  submit(e) {
    e.preventDefault();
    let name = ReactDOM.findDOMNode(this.refs['batchName']);
    if (name.value !== '') {
      this.submitBatchName(name.value);
    }
  },

  render() {
    const uploadButton = (
      this.state.showUploadButton ?
      <button ref="sniffBtn" id="sniff-button" onClick={this.onClickUploadFile}>Sniff</button> :
      ''
    );

    const uploadForm = (
      <form style={{ display: 'none' }} ref="uploadForm" encType="multipart/form-data" action="/upload" method="POST">
        <input ref="fileInput" type="file" id="file" name="file" multiple/>
        <input type="text" value={this.state.fileName || ''} id="file_name" name="file_name"/>
        <input type="text" value={this.state.fileData || ''} id="filedata" name="filedata"/>
        <input type="text" value={this.state.fileUrl || ''} id="fileurl" name="fileurl"/>
        <input type="text" value={this.state.source || ''} id="filesource" name="filesource"/>
        <input type="text" value={this.state.accessToken|| ''} id="accessToken" name="accessToken"/>
      </form>
    );

    const foldersForm = (
      <form style={{ display: 'none' }} ref="foldersForm" encType="multipart/form-data" action="/upload" method="POST">
        <input type="text" value="" id="token" name="token"/>
      </form>
    );

    var bottomDialog;
    if (this.state.preSniff) {
      bottomDialog = (
        <div className="bottom-dialog pre-sniff">
          {uploadButton}
          <div className="external">
            <h2 className="otherApps"> ...or upload from the application of your choice. </h2>
            <UploadApps handleDropbox={this.handleDropboxFile}
                        handleGoogle={this.handleGoogleFile} />
          </div>
        </div>
      );
    }
    else if (this.state.showSummaryPage) {
      bottomDialog = (
        <SummaryPage
          batch={this.state.batchId}
          show={this.state.showSummaryPage}
          reload={this.checkAnalyzedDocs}
          list={this.state.summaryList}
        />
      )
    }
    else if (this.state.askZipPassword) {
      bottomDialog = (
        <ZipPassword
          showZipPassword={this.state.askZipPassword}
          wrongPassword={this.state.zipWrongPassword}
          submitZipPassword={this.onSubmitZipPassword}
          encryptedDocuments={this.state.encryptedDocuments}
          cancel={this.cancelSubmitingZipPassword}
        />
      )
    }
    else if (this.state.showBatchName) {
      bottomDialog = (
        <div className="form-content">
          <div className="form-title">
            Set batch name
          </div>
          <div className="form-body">
            <input placeholder="Chose a name for your batch ..." ref="batchName" maxLength="200" type="text"/>
            <button className="uploadButton" onClick={this.submit}>Upload</button>
            <div className="cancel" onClick={this.closeBatchName}>Cancel</div>
          </div>
        </div>
      )
    }
    else {
      bottomDialog = (
        <div className="bottom-dialog feedback">
          <ul className="feedback-list">
            <li>
              <div className="feedback-icon">
                <ProgressIcon status={this.state.upload} />
              </div>
              <div className="feedback-text">
                <span>Uploading</span>
              </div>
            </li>
            <li>
              <div className="feedback-icon">
                <ProgressIcon status={this.state.conversion} />
              </div>
              <div className="feedback-text">
                <span>Converting</span>
              </div>
            </li>
          </ul>
        </div>
      );
    }

    return (
      <div className="upload-area">
        <DropzoneArea enabled={this.state.preSniff}
                      handleReceivedFiles={this.handleReceivedFiles}
                      totalFilesToUpload={this.state.totalFilesToUpload}
                      fileName={this.state.fileNamesList}
                      filesCount={this.state.fileNamesCount} />
        {uploadForm}
        {bottomDialog}
        {foldersForm}
      </div>
    );
  }
});

const mapUploadAreaComponentStateToProps = (state) => {
  return {
    setting: state.setting
  }
};

const UploadArea = connect(mapUploadAreaComponentStateToProps)(UploadAreaComponent);

const Upload = React.createClass({
  onAccountButtonClick(e) {
    e.preventDefault();
    window.location = '/account#/projects';
  },

  render() {
    const { isInitialized } = this.props;

    return (
      <div className="header-content" >
        <div className="headliner">
          <h2 className="upload-instruction">Upload your document...</h2>
          <button className="account-button" onClick={this.onAccountButtonClick}>Go to my Account</button>
        </div>
        { isInitialized ? <UploadArea {...this.props}/> : '' }
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    isInitialized: state.user.get('isInitialized') && state.setting.get('isInitialized')
  }
};

export default connect(mapStateToProps)(Upload);
