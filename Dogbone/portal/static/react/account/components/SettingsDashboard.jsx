import React from 'react';
import { connect } from 'react-redux';
import Button from 'react-bootstrap/lib/Button';
import classNames from 'classnames';
import ButtonGroup from 'react-bootstrap/lib/ButtonGroup';
import ReactTransitionGroup from 'react-addons-css-transition-group';
import { dropboxAuth } from 'utils/dropboxFolderPicker';
import $ from 'jquery';

// App
import { updateSettings, getFolders } from '../redux/modules/setting';
import DropboxFoldersModal from '../components/DropboxFolderPicker';
import Subscription from './Subscription';
import { getAccessInfo, getGoogleDriveAccessLink, addCloudFolder, revokeGoogleDriveAccess, revokeDropBoxAccess } from '../redux/modules/setting';

/* Component Stylings */
require('./styles/SettingsDashboard.scss');

/* global openFolderPicker */


const ToggleActivateButton = React.createClass({

  onClick(view,e) {
    this.props.onClick(view);
    e.stopPropagation();
  },

  render() {
    var type = this.props.type;
    var button;

    if (type === 'switch') {
      var customizedMsg;
      var toggleStatus = this.props.active ? 'on' : 'off';
      var toggleIconClass = classNames('fa', 'fa-toggle-' + toggleStatus, toggleStatus, this.props.customSetting);
      var toggleButton;
      if (this.props.customized) {
        customizedMsg = (
          <div className="customized-msg">
            (custom)
          </div>
        );
        toggleButton = (
          <span className="custom-toggle-stack">
            <i className="fa fa-toggle-on stack-canvas" />
            <i className="fa fa-asterisk stack-asterisk" />
          </span>
        );
      } else {
        toggleButton = (
          <i className={toggleIconClass} />
        );
      }
      button = (
        <span className="toggleActiveButton" onClick={(e) => this.onClick(!this.props.active,e)}>
          {toggleButton}
          {customizedMsg}
        </span>
      );
    } else {
      switch (this.props.active) {
      case '#/widget-panel': {
        var widgetActive = true;
        break;
      }
      case '#/detail-view': {
        var detailActive = true;
        break;
      }
      case '#/clause-table': {
        var clauseActive = true;
        break;
      }
      case '#/context-view': {
        var contextActive = true;
        break;
      }
      default: {
        break;
      }
      }

      button = (
        <ButtonGroup className="report-view">
          <Button className="view-button" active = {widgetActive} onClick={(e) => this.onClick('#/widget-panel', e)}>
            <div className="view-icon">
              <i className="fa fa-tachometer" aria-hidden="true" />
            </div>
            <div className="view-text">
              Widget Panel
            </div>
          </Button>
          <Button className="view-button" active = {detailActive} onClick={(e) => this.onClick('#/detail-view', e)}>
            <div className="view-icon">
              <i className="fa fa-file-alt" aria-hidden="true" />
            </div>
            <div className="view-text">
              Detail View
            </div>
          </Button>
          <Button className="view-button" active = {clauseActive} onClick={(e) => this.onClick('#/clause-table', e)}>
            <div className="view-icon">
              <i className="fa fa-list-alt" aria-hidden="true" />
            </div>
            <div className="view-text">
              Clause Table
            </div>
          </Button>
          <Button className="view-button" active = {contextActive} onClick={(e) => this.onClick('#/context-view', e)}>
            <div className="view-icon">
              <i className="fa fa-columns" aria-hidden="true" />
            </div>
            <div className="view-text">
              Context View
            </div>
          </Button>
        </ButtonGroup>
      );
    }

    return (
      <span>
        {button}
      </span>
    );
  }
});

const CustomNotifListItem = React.createClass({

  toggleActive() {
    this.props.toggle(!this.props.active);
  },

  render() {
    const activation = (
      <ToggleActivateButton
        active={this.props.active}
        onClick={this.toggleActive}
        type={'switch'}
        customSetting={'custom-setting-toggle-button'}
      />
    );

    return (
      <div className="custom-setting">
        <div className="custom-title">
          {this.props.title}
        </div>
        <div className="custom-title switch">
          {activation}
        </div>
        <SettingStatusIcon active={this.props.active} />
      </div>
    );
  }
});

const SettingStatusIcon = React.createClass({

  getInitialState() {
    return {
      isVisible: false
    }
  },

  componentWillReceiveProps(nextProps) {
    const { active, customized, applySysDefaultView } = this.props;
    // When active OR customized property is changed show status icon
    // Boolean check is needed to avoid undefined or null values
    if (typeof active === 'boolean' && active !== nextProps.active ||
        typeof active === 'string' && applySysDefaultView === false && active !== nextProps.active ||
        typeof customized === 'boolean' && customized !== nextProps.customized) {
      // when icon is still visible clear timeout for its hiding
      if (this.statusIconTimeoutId) clearTimeout(this.statusIconTimeoutId)

      // show status icon
      this.setState({ isVisible: true })
      this.statusIconTimeoutId = setTimeout(() => {
        this.setState({ isVisible: false })
        this.statusIconTimeoutId = null;
      }, this.statusIconTimeout)
    }
  },

  componentWillUnmount() {
    if (this.statusIconTimeoutId) {
      clearInterval(this.statusIconTimeoutId)
    }
  },

  statusIconTimeout: 1500,
  statusIconTimeoutId: null,

  render() {
    return (
      <ReactTransitionGroup transitionName="setting-status"
          transitionEnterTimeout={100}
          transitionLeaveTimeout={100}>
          { this.state.isVisible && <i className="setting-status-icon fa fa-check" /> }
      </ReactTransitionGroup>
    )
  }
})

const SettingListItem = React.createClass({
  getInitialState() {
    return {
      detailes: this.props.expanded
    };
  },

  toggleDetails() {
    this.setState({ detailes: !this.state.detailes });
  },

  render() {
    const settingName = this.props.settingName;
    var dropdown;
    var additionalDropdown = this.props.additionalDropdown && this.props.additionalDropdown;
    if (this.props.dropdown || this.props.watcher) {
      if (this.state.detailes) {
        dropdown = (
          <i className="fa fa-angle-double-up" aria-hidden="true" style={{ float: 'right', color: '#5d101a' }} />
        );
      } else {
        dropdown = (
          <i className="fa fa-angle-double-down" aria-hidden="true" style={{ float: 'right', color: '#5d101a' }} />
        );
      }
    }

    var activation = (
        <span>
          <ToggleActivateButton active={this.props.active} customized={this.props.customized} onClick={this.props.onChange} type={this.props.type}/>
          {dropdown}
        </span>
    );

    var optionalSettings;
    if (this.props.dropdown) {
      optionalSettings=(
        <ul className="custom-list">
          <li><CustomNotifListItem
                active={this.props.activeFinishProcesEmailNotif}
                title="Document or Batch processing finished"
                toggle={this.props.onFinishProcesEmailNotif}
              />
          </li>
          <li><CustomNotifListItem
                active={this.props.activeColabInvEmailNotif}
                title="Collaboration invite received"
                toggle={this.props.onColabInvEmailNotif}
              />
          </li>
          <li><CustomNotifListItem
                active={this.props.activeCommMentionEmailNotif}
                title="Mentioned in a comment"
                toggle={this.props.onCommMentionEmailNotif}
              />
          </li>
          <li><CustomNotifListItem
                active={this.props.activeOwnChangeEmailNotif}
                title="Owner changed"
                toggle={this.props.onOwnChangeEmailNotif}
              />
          </li>
        </ul>
      );
    } else if (this.props.watcher) {
      optionalSettings=(
        <span>
          {this.props.active && additionalDropdown}
        </span>
      );
    }

    var detailes;
    if (this.state.detailes) {
      detailes=(
        <div className="dropdown">
          {this.props.detailes}
          {optionalSettings}
        </div>
      );
    }
    var detailesWrapper;
    if (this.props.dropdown) {
      detailesWrapper = (
        <ReactTransitionGroup
          transitionName="detail_dropdown"
          transitionEnterTimeout={80}
          transitionLeaveTimeout={80}>
          {detailes}
        </ReactTransitionGroup>
      );
    } else if (this.props.watcher && this.props.active) {
      detailesWrapper = (
        <ReactTransitionGroup
          transitionName="detail_dropdown_watcher"
          transitionEnterTimeout={80}
          transitionLeaveTimeout={80}>
          {detailes}
        </ReactTransitionGroup>
      );
    } else {
      detailesWrapper = (
        <ReactTransitionGroup transitionName="detail"
          transitionEnterTimeout={80}
          transitionLeaveTimeout={80}>
          {detailes}
        </ReactTransitionGroup>
      );
    }

    const rowClassName = classNames('settings-row', {
      'settings-row-group': this.props.type === 'group'
    });

    return (
      <div className="setting-wrapper">
        <div className={rowClassName} onClick={this.toggleDetails}>
          <div className="setting-name">
            {settingName}
          </div>
          {activation}
          <SettingStatusIcon
            active={this.props.active}
            customized={this.props.customized}
            applySysDefaultView={this.props.applySysDefaultView} />
        </div>
        {detailesWrapper}
      </div>
    );
  }
});

const FolderWatcher = React.createClass({
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
                      {value.title}
                    </div>
                    <div className="delete-folder" onClick={(e) => {deleteFolder(value.id,e)}}>
                      Untrack folder <i className="fa fa-times" aria-hidden="true"/>
                    </div>
                  </div>
                )
              })
            }
          </div>
        </div>
          <div className="drive-action" onClick={openFolderPicker}>
            <i className="fa fa-plus" aria-hidden="true"/> Add new folder
          </div>
        <div className="drive-action critical" onClick={revokeAccess}>
          <i className="fa fa-times" aria-hidden="true"/>Revoke Access
        </div>
        {modal}
      </div>
    )
  }
})

const SettingsDashboard = React.createClass({
  getInitialState() {
    return {
      showFolderPicker: false,
      showDropboxConfigModal: false,
      cloud: 'google',
    };
  },

  openDropboxConfig(e) {
    dropboxAuth();
    e.stopPropagation();
  },

  refreshFolders() {
    const { dispatch } = this.props;
    dispatch(getFolders());
  },

  onFinishProcesEmailNotif(state) {
    Intercom('trackUserEvent', 'toggle-finish-processing-notification');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      finished_processing_notification: state
    }));
  },

  onColabInvEmailNotif(state) {
    Intercom('trackUserEvent', 'toggle-colabortation-invite-notification');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      collaboration_invite_notification: state
    }));
  },

  onCommMentionEmailNotif(state) {
    Intercom('trackUserEvent', 'toggle-comment-mention-notification');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      comment_mention_notification: state
    }));
  },

  onOwnChangeEmailNotif(state) {
    const { dispatch } = this.props;

    Intercom('trackUserEvent', 'toggle-owner-change-notification');

    dispatch(updateSettings({
      owner_changed_notification: state
    }));
  },

  toggleAll() {
    const { dispatch, settings } = this.props;

    Intercom('trackUserEvent', 'toggle-all-email-notifications');
    let state
    if (settings.get('email_notification_customized')) {
      state = true
    } else {
      state = !settings.get('email_notification_active');
    }

    dispatch(updateSettings({
      finished_processing_notification: state,
      collaboration_invite_notification: state,
      comment_mention_notification: state,
      owner_changed_notification: state
    }));
  },

  onChangeEmailDigest(state) {
    Intercom('trackUserEvent', 'toggle-email-digest');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      email_digest_notification: state
    }));
  },

  onChangeIncludeClause(state) {
    Intercom('trackUserEvent', 'toggle-email-include-clause');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      include_clause_in_outcoming_mention_emails: state
    }));
  },

  onChangeDefaultRepView(view) {
    Intercom('trackUserEvent', 'change-default-report-view');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      default_report_view: view
    }));
  },

  onChangeOnlineFolderView(view) {
    Intercom('trackUserEvent', 'online-folder-watcher');

    const { dispatch } = this.props;
    dispatch(updateSettings({
      online_folder_watcher: view
    }));
  },

  openGdriveFolderPicker(e) {
    const { dispatch } = this.props;
    openFolderPicker((data) => {
      let dataToSend = {
        folder_id: data.id,
        title: data.name,
        cloud: 'google_drive',
      }
      dispatch(addCloudFolder(dataToSend))
        .then(() => {
          this.refreshFolders();
        });
    });
    e.stopPropagation();
  },

  saveDropboxFolder(id, path, title) {
    const { dispatch } = this.props;
    let dataToSend = {
      folder_id: id,
      title: title,
      'folder_path': path,
      cloud: 'dropbox',
    }
    dispatch(addCloudFolder(dataToSend))
      .then(() => {
        this.refreshFolders();
      });
  },

  closeFolderPicker() {
    this.setState({
      showFolderPicker: false
    })
  },

  openFolderPicker(e) {
    this.setState({
      showFolderPicker: true
    })

    e.stopPropagation();
  },

  deleteFolder(id,e) {
    const formData = new FormData();
    formData.append('id', id);
    $.ajax({
      url: '/api/v1/upload/delete_cloud_folder',
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false
    })
      .always(() => {
        this.refreshFolders();
      });
    e.stopPropagation();
  },

  updateAccessState() {
    const { dispatch } = this.props;
    dispatch(getAccessInfo());
  },

  getLink(e) {
    const { dispatch } = this.props;
    dispatch(getGoogleDriveAccessLink())
      .then(response => {
        location.href = response.data.accessUrl;
      });
    e.stopPropagation();
  },

  revokeGoogleDriveAccess(e) {
    const { dispatch } = this.props;
    dispatch(revokeGoogleDriveAccess())
    e.stopPropagation();
  },

  revokeDropBoxAccess(e) {
    const { dispatch } = this.props;
    dispatch(revokeDropBoxAccess())
    e.stopPropagation();
  },

  render() {
    const emailNotifDetails = 'Email notifications can be a convenient way of being up to date';
    const emailDigestDetailes = 'An Email digest of pending notifications can quickly get you up to speed with the activity on your documents';
    const emailIncludeClauseDetailes = 'Include commented clause in outbound invite emails';
    const defaultRepView = 'Choose what\'s the first screen going to be when entering a document';
    const onlineFolderWatcherDescription = 'Choose if you want to add watcher to your folders';

    const { settings, subscription, user } = this.props;
    const cloud_access = settings.get('cloud_acces_info').toJS();

    var gdriveFoldersList = settings.get('cloud_folders').toJS().filter((item) => {
      return item.cloud === 'google_drive';
    })

    var dropboxFoldersList = settings.get('cloud_folders').toJS().filter((item) => {
      return item.cloud === 'dropbox'
    })

    const isInitialized = settings.get('isInitialized');
    const isAccessInfoInitialized = !$.isEmptyObject(cloud_access);

    const settingNameNotif = (
      <div>
        <div className="setting-icon">
          <i className="fa fa-bell" aria-hidden="true" />
        </div>
        <div className="setting-title">
          Email notifications
        </div>
      </div>
    );

    const settingNameDigest = (
      <div>
        <div className="setting-icon">
          <i className="fa fa-envelope" aria-hidden="true" />
        </div>
        <div className="setting-title">
          Email digest
        </div>
      </div>
    );

    const settingNameIncludeClause = (
      <div>
        <div className="setting-icon">
          <i className="fa fa-align-left" aria-hidden="true" />
        </div>
        <div className="setting-title">
          Include clause in Invite Emails
        </div>
      </div>
    );

    const settingNameRep = (
      <div>
        <div className="setting-icon">
          <i className="fa fa-eye" aria-hidden="true" />
        </div>
        <div className="setting-title">
          Default report view
        </div>
      </div>
    );

    const settingNameFolder = (
      <div>
        <div className="setting-icon">
          <i className="fa fa-folder" aria-hidden="true" />
        </div>
        <div className="setting-title">
          Online folder watcher
        </div>
      </div>
    );

    const googleDrive = (
      <FolderWatcher
        title={(<span><i className="fab fa-google-drive" aria-hidden="true" />Google Drive</span>)}
        foldersList={gdriveFoldersList}
        deleteFolder={this.deleteFolder}
        openFolderPicker={this.openGdriveFolderPicker}
        revokeAccess={this.revokeGoogleDriveAccess}
      />
    );

    const dropbox = (
      <FolderWatcher
        title={(<span><i className="fab fa-dropbox" aria-hidden="true" />Dropbox</span>)}
        foldersList={dropboxFoldersList}
        deleteFolder={this.deleteFolder}
        openFolderPicker={this.openFolderPicker}
        revokeAccess={this.revokeDropBoxAccess}
        modal={(<DropboxFoldersModal token={cloud_access.token} handleSelect={this.saveDropboxFolder} folderPickerState={this.state.showFolderPicker} closeFolderPicker={this.closeFolderPicker}/>)}
      />
    )
    const currentSubscription = subscription.get('current_subscription');
    const isSuper = user.get('is_super');

    const googleDriveIsLoading = settings.get('googleDriveIsLoading');
    const folders = currentSubscription || isSuper ?
      (<div className="folders-watcher-wraper">
        <div className="folder-wraper">
          {cloud_access['google-drive'] ?
            googleDrive :
            <div className="access-button" onClick={this.getLink}>
              <i className="fab fa-google-drive" aria-hidden="true" />
              {googleDriveIsLoading ? 'Loading' : 'Set Google Drive access'}
            </div>
          }
        </div>
        <div className="folder-wraper">
          {cloud_access['dropbox'] ?
            dropbox :
            <div className="access-button" onClick={this.openDropboxConfig}>
              <i className="fab fa-dropbox" aria-hidden="true" />
              Set Dropbox access
            </div>
          }
        </div>
      </div>) :
      (<div className="folders-watcher-wraper">
        <div className="folder-wraper disabled">
          <span className = "warning-sign">
            <i className="fa fa-exclamation-triangle" aria-hidden="true" />
          </span>
          You can't use this feature while no subscription is active
        </div>
      </div>);

    const emailNotification = settings.get('email_notification_active');
    const finishedProcessingNotification = settings.get('finished_processing_notification');
    const colaborationInviteNotification = settings.get('collaboration_invite_notification');
    const commentMentionNotification = settings.get('comment_mention_notification');
    const ownerChangedNotification = settings.get('owner_changed_notification');
    const emailDigestNotification = settings.get('email_digest_notification');
    const emailIncludeClause = settings.get('include_clause_in_outcoming_mention_emails');
    const applySysDefaultView = !settings.get('default_report_view');
    const defaultReportView = settings.get('default_report_view') || '#/widget-panel';
    const onlineFolderWatcher = settings.get('online_folder_watcher');

    let pageContent;

    if (!isInitialized || !isAccessInfoInitialized) {
      pageContent = (
        <div>
          <div className="settings-column">
            <div className="settings-listing-no-data">
              <i className="fa fa-cog fa-spin"/>
              <div className="settings-message">Loading</div>
            </div>
          </div>
        </div>
      );
    } else {
      pageContent = (
        <div className="settings-column">
          <div className="settings-container">
            <SettingListItem
              expanded={false}
              dropdown={true}
              settingName={settingNameNotif}
              active={emailNotification}
              customized={settings.get('email_notification_customized')}
              activeFinishProcesEmailNotif={finishedProcessingNotification}
              activeColabInvEmailNotif={colaborationInviteNotification}
              activeCommMentionEmailNotif={commentMentionNotification}
              activeOwnChangeEmailNotif={ownerChangedNotification}
              type={'switch'}
              onFinishProcesEmailNotif={this.onFinishProcesEmailNotif}
              onColabInvEmailNotif={this.onColabInvEmailNotif}
              onCommMentionEmailNotif={this.onCommMentionEmailNotif}
              onOwnChangeEmailNotif={this.onOwnChangeEmailNotif}
              onChange={this.toggleAll}
              detailes={emailNotifDetails}
            />
            <SettingListItem
              expanded={false}
              settingName={settingNameDigest}
              active={emailDigestNotification}
              type={'switch'}
              onChange={this.onChangeEmailDigest}
              detailes={emailDigestDetailes}
            />
            <SettingListItem
              expanded={false}
              settingName={settingNameIncludeClause}
              active={emailIncludeClause}
              type={'switch'}
              onChange={this.onChangeIncludeClause}
              detailes={emailIncludeClauseDetailes}
            />
            <SettingListItem
              expanded={false}
              settingName={settingNameRep}
              type={'group'}
              active={defaultReportView}
              onChange={this.onChangeDefaultRepView}
              detailes={defaultRepView}
              applySysDefaultView={applySysDefaultView}
            />
            <SettingListItem
              expanded={true}
              watcher={true}
              settingName={settingNameFolder}
              type={'switch'}
              active={onlineFolderWatcher}
              onChange={this.onChangeOnlineFolderView}
              detailes={onlineFolderWatcherDescription}
              additionalDropdown={folders}
            />
            <Subscription />
          </div>
        </div>
      )
    }

    return (
      <div>
        <div className="settings-title">
          Account Settings
        </div>
        {pageContent}
      </div>
    );
  }
});


const mapSettingsDashboardStateToProps = (state) => {
  return {
    user: state.user,
    settings: state.setting,
    subscription: state.subscription
  }
};

export default connect(mapSettingsDashboardStateToProps)(SettingsDashboard)
