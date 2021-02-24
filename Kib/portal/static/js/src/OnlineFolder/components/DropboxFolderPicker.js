
import React from 'react';

// Bootstrap
import Button from 'react-bootstrap/lib/Button';
import Modal from 'react-bootstrap/lib/Modal';
import ButtonToolbar from 'react-bootstrap/lib/ButtonToolbar';

//Utils
import DropboxApi from 'base/utils/dropboxFolderPicker.js';

require('../scss/DropboxFolderPicker.scss');

const DropboxFolder = React.createClass({
  propTypes: {
    value: React.PropTypes.object,
    openFolder: React.PropTypes.func,
    storeCurrentPath: React.PropTypes.func,
    selected: React.PropTypes.bool
  },

  handleOpenFolder() {
    const { openFolder, value, storeCurrentPath } = this.props;
    openFolder(value.path_lower);
    storeCurrentPath(value.path_lower);
  },

  handleFolderSelect() {
    const { selectFolder, value } = this.props;
    selectFolder(value.id, value.path_lower, value.name);
  },

  render() {
    const { value } = this.props;
    const dropboxFolder = this.props.selected ? 'dropbox-folder selected' : 'dropbox-folder'

    return (
      <div className={dropboxFolder} onClick={this.handleFolderSelect} onDoubleClick={this.handleOpenFolder}>
        <div>
          <i className="fa fa-folder-o dropbox-folder-image" aria-hidden="true"/>
        </div>
        <div className="dropbox-info">
          <div className="dropbox-folder-name" >
            <span>
              {value.name}
            </span>
          </div>
        </div>
      </div>
    );
  }
});

const DropboxFoldersList = React.createClass({

  reverse(string) {
    return string.split('').reverse().join('');
  },

  handleBackFolder() {
    const { openFolder, setCurrentPath } = this.props;
    let { currentPath } = this.props;
    currentPath = this.reverse(currentPath);
    currentPath = currentPath.substring(currentPath.indexOf('/')+1, currentPath.length);
    currentPath = this.reverse(currentPath);
    openFolder(currentPath)
    setCurrentPath(currentPath);
  },

  handleSelectFolder(id, path, title) {
    this.props.checkFolder(id, path, title);
  },

  render() {
    const { folders, openFolder, setCurrentPath } = this.props;
    const backButton = (
      <div className="dropbox-folder" onClick={this.handleBackFolder}>
        <div>
          <i className="fal fa-folder-open dropbox-folder-image" aria-hidden="true" />
        </div>
        <div className="dropbox-info">
          <div className="dropbox-folder-name" >
            <span>
              ...
            </span>
          </div>
        </div>
      </div>
    );
    var FoldersList;
    if (folders.length) {
      FoldersList = (
        folders.map((v, k) => {
          return (<DropboxFolder
            openFolder={openFolder}
            selectFolder={this.handleSelectFolder}
            selected={this.props.checkedFolder === v.id}
            storeCurrentPath={setCurrentPath}
            value={v}
            key={k}/>);
        })
      );
    } else {
      FoldersList = (
        <div className="emptyFolder">
          <img src="/static/img/this-folder-is-empty-dropbox.jpg"/>
        </div>
      );
    }

    return (
      <div>
        {this.props.isFetching ?
          <div className="loader"></div> : 
          (
            <span>
              {backButton}
              {FoldersList}
            </span>
          )
        }
      </div>
    );
  }
});

const DropboxFoldersModal = React.createClass({
  propTypes: {
    openFolderPicker: React.PropTypes.func,
    folderPickerState: React.PropTypes.bool,
    handleSelect: React.PropTypes.func
  },

  getInitialState() {
    return {
      currentPath:'',
      folders: null,
      selectedFolderId: null,
      selectedFolderPath: null,
      selectedFolderTitle: null,
      isFetching: false,
    }
  },

  componentDidMount() {
    this.getFolders('');
  },

  setCurrentPath(path) {
    this.setState({
      currentPath: path
    })
  },

  getFolders(path) {
    this.setState({
      isFetching: true,
    });
    DropboxApi.getFolders(path, this.props.token)
      .then(response => {
        this.filterFolders(response.entries);
        this.selectFolder(null, null);
        this.setState({
          isFetching: false,
        })
      })
      .catch(() => {
        this.setState({
          isFetching: false,
        })
      });
  },

  isFolder(value) {
    return value['.tag'] === 'folder';
  },

  filterFolders(items) {
    this.setState({
      folders: items.filter(this.isFolder)
    });
  },

  selectFolder(folderId, path, title) {
    if (this.state.selectedFolderId === folderId) {
      this.setState({
        selectedFolderId: null,
        selectedFolderPath: null,
        selectedFolderTitle: null,
      });
    } else {
      this.setState({
        selectedFolderId: folderId,
        selectedFolderPath: path,
        selectedFolderTitle: title,
      })
    }
  },

  open() {
    const { selectedFolderPath } = this.state;
    this.setCurrentPath(selectedFolderPath);
    this.getFolders(selectedFolderPath);
  },

  submit() {
    const { selectedFolderId, selectedFolderPath, selectedFolderTitle } = this.state;
    this.props.handleSelect(selectedFolderId, selectedFolderPath, selectedFolderTitle);
    this.props.closeFolderPicker();
  },

  render() {
    return (
      <Modal show={this.props.folderPickerState} onHide={this.props.closeFolderPicker} className="watcher-dialog">
        <Modal.Header>
          <div className="dropbox-logo">
            <i className="fab fa-dropbox" aria-hidden="true" />
          </div>
          <div className="close" onClick={this.props.closeFolderPicker}>
            <i className="fal fa-times close-modal-folder" aria-hidden="true" />
          </div>
        </Modal.Header>
        <Modal.Body>
          <div className="body-wrapper">
            <DropboxFoldersList
              folders={this.state.folders}
              openFolder={this.getFolders}
              checkFolder={this.selectFolder}
              checkedFolder={this.state.selectedFolderId}
              isFetching={this.state.isFetching}
              currentPath={this.state.currentPath}
              setCurrentPath={this.setCurrentPath}/>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <ButtonToolbar>
            {
              this.state.selectedFolderId
              ? <Button className="activeButton" onClick={this.submit} bsStyle="success">Select</Button>
              : <Button disabled>Select</Button>
            }
            {
              this.state.selectedFolderId
              ? <Button className="activeButton" onClick={this.open}>Open</Button>
              : <Button disabled>Open</Button>
            }
            <Button onClick={this.props.closeFolderPicker}>Close</Button>
          </ButtonToolbar>
        </Modal.Footer>
      </Modal>
    );
  }

});

module.exports = DropboxFoldersModal;
