import React from 'react';
import { connect } from 'react-redux';

import { dropboxAuth } from 'base/utils/dropboxFolderPicker.js'
import { getAccessInfo, getGoogleDriveAccessLink, getFolders, addCloudFolder, revokeDropBoxAccess, revokeGDriveAccess, untrackDropboxFolder } from '../redux/modules/onlineFolder.js'
import DropboxFoldersModal from './DropboxFolderPicker.js';
import { Panel, ButtonToolbar, Button, Grid, Col, Modal } from 'react-bootstrap';
import { Spinner } from 'base/components/misc'

import '../scss/PickerPanel.scss'

class FolderWatcher extends React.Component{
  render() {
    const { title, foldersList, deleteFolder, openFolderPicker, revokeAccess, modal } = this.props;
    return (
      <div className="folder-container">
        <div className="drive-icon">
          {title}
        </div>
        <div className="drive-body">
          <div className="drive-folder-list">
            {
              foldersList.map((value, key) => {
                return (
                  <div key={key} className="list-item">
                    <div className="folder-name" title={value.title}>
                      {value.folder_path}
                    </div>
                    <div className="delete-folder" onClick={(e) => {deleteFolder(value.id,e)}}>
                      Untrack folder <i className="far fa-times" aria-hidden="true"/>
                    </div>
                  </div>
                )
              })
            }
          </div>
        </div>
        <div className="drive-action" onClick={openFolderPicker}>
          <i className="far fa-plus" aria-hidden="true"/> Add new folder
        </div>
        <div className="drive-action critical" onClick={revokeAccess}>
          <i className="far fa-times" aria-hidden="true"/>Revoke Access
        </div>
        {modal}
      </div>
    )
  }
}

class PickerPanel extends React.Component {

  constructor(props) {
    super(props);
    this.opneModal = this.opneModal.bind(this);
    this.closeModal = this.closeModal.bind(this);
    this.closeFolderPicker = this.closeFolderPicker.bind(this);
    this.openFolderPicker = this.openFolderPicker.bind(this);
    this.refreshFolders = this.refreshFolders.bind(this);
    this.saveDropboxFolder = this.saveDropboxFolder.bind(this);
    this.revokeDropBoxAccess = this.revokeDropBoxAccess.bind(this);
    this.untrackDropboxFolder = this.untrackDropboxFolder.bind(this);
    this.getLink = this.getLink.bind(this);
    this.openGdriveFolderPicker = this.openGdriveFolderPicker.bind(this);
    this.revokeGDriveAccess = this.revokeGDriveAccess.bind(this);
    this.state = {
      showDropboxModal:false,
      showFolderPicker:false,
      modal:false
    }
  }

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(getAccessInfo());
    dispatch(getFolders());
  }

  openDropboxConfig(e) {
    dropboxAuth();
    e.stopPropagation();
  }

  getLink(e) {
    const cloud_access = this.props.OnlineFolder.get('cloud_acces_info').toJS();
    location.href = cloud_access['google_drive'].auth_url;
    e.stopPropagation();
  }

  openGdriveFolderPicker(e) {
    const { dispatch } = this.props;
    openFolderPicker((data) => {
      let dataToSend = {
        folder_id: data.id,
        folder_path: data.name,
        cloud: 'google_drive',
      }
      dispatch(addCloudFolder(dataToSend))
        .then(() => {
          this.refreshFolders();
        });
    });
    e.stopPropagation();
  }

  opneModal(modal) {
    this.setState({
      showDropboxModal:true,
      modal: modal
    })
  }

  closeModal() {
    this.setState({
      showDropboxModal:false
    })
  }

  openFolderPicker() {
    this.setState({
      showFolderPicker:true
    })
  }

  closeFolderPicker() {
    this.setState({
      showFolderPicker: false
    })
  }

  refreshFolders() {
    const { dispatch } = this.props;
    dispatch(getFolders());
  }

  saveDropboxFolder(id, path, title) {
    const { dispatch } = this.props;
    let dataToSend = {
      folder_id: id,
      folder_path: path,
      cloud: 'dropbox',
    }
    dispatch(addCloudFolder(dataToSend))
      .then(() => {
        this.refreshFolders();
      });
  }

  revokeDropBoxAccess(e) {
    const { dispatch } = this.props;
    dispatch(revokeDropBoxAccess());
    e.stopPropagation();
  }

  revokeGDriveAccess(e) {
    const { dispatch } = this.props;
    dispatch(revokeGDriveAccess());
    e.stopPropagation();
  }

  untrackDropboxFolder(id,e) {
    const { dispatch } = this.props;
    dispatch(untrackDropboxFolder(id));
    e.stopPropagation();
  }

  render() {
    const cloud_access = this.props.OnlineFolder.get('cloud_acces_info').toJS();
    const dropboxFoldersList = this.props.OnlineFolder.get('cloud_folders').toJS().filter((item) => {
      return item.cloud === 'dropbox'
    })
    const gdriveFoldersList = this.props.OnlineFolder.get('cloud_folders').toJS().filter((item) => {
      return item.cloud === 'google_drive'
    })

    const isInitialized = this.props.OnlineFolder.get('isInitialized')

    return (
      <div>
        <Panel>
          <Grid>
            <Col xs={12} md={12}>
              {isInitialized ? 
                <div className="folder-watchers">
                  <div className="watcher-wrapper">
                    {cloud_access['google_drive'] && cloud_access['google_drive'].access ?
                      <FolderWatcher
                        title={(<span><i className="fab fa-google" aria-hidden="true" />Google Drive</span>)}
                        foldersList={gdriveFoldersList}
                        deleteFolder={this.untrackDropboxFolder}
                        openFolderPicker={this.openGdriveFolderPicker}
                        revokeAccess={this.revokeGDriveAccess}
                      /> :
                      <ButtonToolbar>
                        <Button bsSize="small" bsStyle="primary" onClick={this.getLink}>
                          <div className="cloud-icons-button white-icon"><i className="fab fa-google" aria-hidden="true"></i></div>
                          Allow Google Drive Access
                        </Button>
                      </ButtonToolbar>
                    }
                  </div>
                  <div className="watcher-wrapper">
                    {cloud_access['dropbox'] && cloud_access['dropbox'].access ?
                      <FolderWatcher
                        title={(<span><i className="fab fa-dropbox" aria-hidden="true" />Dropbox</span>)}
                        foldersList={dropboxFoldersList}
                        deleteFolder={this.untrackDropboxFolder}
                        openFolderPicker={this.openFolderPicker}
                        revokeAccess={this.revokeDropBoxAccess}
                        modal={(<DropboxFoldersModal token={cloud_access.dropbox && cloud_access.dropbox.token} handleSelect={this.saveDropboxFolder} folderPickerState={this.state.showFolderPicker} closeFolderPicker={this.closeFolderPicker}/>)}
                      /> :
                      <ButtonToolbar>
                        <Button bsSize="small" bsStyle="primary" onClick={this.openDropboxConfig}>
                          <div className="cloud-icons-button white-icon"><i className="fab fa-dropbox" aria-hidden="true"></i></div>
                          Allow Dropbox Access
                        </Button>
                      </ButtonToolbar>
                    }
                  </div>
                </div>
                :
                <Spinner/>
              }
            </Col>
          </Grid>
        </Panel>
      </div>
    );
  }
}

PickerPanel.defaultProps = {
};

const mapStateToProps = (state) => {
  return {
    OnlineFolder: state.onlineFolder
  };
};

export default connect(mapStateToProps)(PickerPanel);
