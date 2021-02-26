import React from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import FormGroup from 'react-bootstrap/lib/FormGroup';
import FormControl from 'react-bootstrap/lib/FormControl';
import ControlLabel from 'react-bootstrap/lib/ControlLabel';
import Button from 'react-bootstrap/lib/Button';
import AvatarEditor from 'react-avatar-editor';
import { hashHistory } from 'react-router';

// App
import Spinner from 'common/components/Spinner';
import { Notification } from 'common/redux/modules/transientnotification';
import { updateProfileData } from 'common/redux/modules/user';

/* Component Stylings */
require('./styles/EditProfile.scss');    //stylings for component

/**
 * Convert an image to a base64 url
 * thanks http://stackoverflow.com/a/20285053
 * @param  {String}   url
 * @param  {Function} callback
 * @param  {String}   [outputFormat=image/png]
 */
function convertImgToBase64URL(url, callback, outputFormat) {
  var img = new Image();
  img.crossOrigin = 'Anonymous';
  img.onload = function() {
    let canvas = document.createElement('CANVAS');
    canvas.height = img.height;
    canvas.width = img.width;

    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0);

    const dataURL = canvas.toDataURL(outputFormat);
    callback(dataURL);
    canvas = null;
  };
  img.src = url;
}


const EditAvatarForm = React.createClass({
  getInitialState() {
    const user = this.props.user.toJS();
    const imgURL = user.avatar;
    let profileSrc = imgURL;
    convertImgToBase64URL(imgURL, (dataURL) => {
      profileSrc = this.setImgBase64(dataURL);
    });

    return {
      profileSrc,
      updated: false,
      scale: 1
    };
  },

  setImgBase64(dataURL) {
    this.setState({ profileSrc: dataURL });
    return dataURL;
  },

  handleUpdate() {
    var key = 'profileSrc';
    var value = null;
    if (this.state.updated) {
      value = this.refs.avatarEditor.getImage().toDataURL();
    }
    this.props.changeFormState(key, value, this.props.editUser);
  },

  displayProfilePicture() {
    var self = this;
    var formReader = new FileReader();
    formReader.readAsDataURL(ReactDOM.findDOMNode(this.refs.uploadImg).files[0]);

    formReader.onload = function(e) {
      var dataURL = e.target.result;
      self.setImgBase64(dataURL);
    };

    //the profile picture has changed
    this.setState({
      updated : true
    });
  },

  onRangeChange(ev) {
    this.setState({ scale: parseFloat(ev.target.value), updated: true });
  },

  render() {
    return (
      <div className="profile-column edit-profile-avatar-column">
        <div className="edit-profile-section">
          <div className="edit-profile-avatar-container">
            <AvatarEditor
              image={this.state.profileSrc}
              width={170}
              height={170}
              border={20}
              scale={this.state.scale}
              ref="avatarEditor"
            />
          </div>
          <div className="edit-profile-avatar-upload-container">
            <form encType="multipart/form-data" ref="theForm" id="theForm" action="/upload_profile_picture" method="POST">
              <input
                onChange={this.displayProfilePicture}
                ref="uploadImg"
                type="file"
                name="avatar"
                accept="image/*"
              />
              <input
                type="range"
                min="1"
                max="2"
                step="0.01"
                value={this.state.scale || '1'}
                ref="range"
                onChange={this.onRangeChange}
              />
            </form>
          </div>
          <UpdateButtons
            onUpdate={this.handleUpdate}
            onCancel={this.props.setProjectView} />
        </div>
      </div>
    );
  }
});


const UpdateButtons = ({ onUpdate, onCancel }) => {
  return (
    <div className="edit-profile-update-buttons">
      <Button
        bsStyle="success"
        onClick={onUpdate}>Update</Button>
      <a href="/account#/projects">
        <Button
          className="edit-profile-cancel-button"
          onClick={onCancel}>Cancel</Button>
      </a>
    </div>
  )
}


const EditProfileForm = React.createClass({
  /*Set the state of the changed textbox to the value the user inputs*/
  handleChange(event) {
    const key = event.target.id;
    const value = event.target.value;
    this.props.changeFormState(key, value);
  },

  render() {
    const first = this.props.first;
    const last = this.props.last;
    const phone = this.props.phone;
    const title = this.props.title;
    const company = this.props.company;
    const oldpass = this.props.oldpass;
    const newpass = this.props.newpass;
    const confirmnewpass = this.props.confirmnewpass;
    const fbsStyle = this.props.first_error ? 'error' : 'default';
    const lbsStyle = this.props.last_error ? 'error' : 'default';

    return (
      <div className="projects-column edit-profile-column">
        <div className="edit-profile-header">
          <div className="edit-profile-title-container">
            <span className="edit-profile-chevron">
              <i className="fa fa-chevron-right"/>
            </span>
            <span className="edit-profile-title">Edit Profile</span>
          </div>
        </div>
        <div className="edit-profile-body">
          <div className="edit-profile-section">
            <FormGroup>
              <div className="adjacent">
                <div className="adjacent-column">
                  <ControlLabel>First Name</ControlLabel>
                  <FormControl
                    type="text"
                    bsStyle={fbsStyle}
                    id="first"
                    value={first || ''}
                    onChange={this.handleChange}
                    placeholder="First Name"
                  />
                </div>
                <div className="adjacent-column">
                  <ControlLabel>Last Name</ControlLabel>
                  <FormControl
                    type="text"
                    bsStyle={lbsStyle}
                    id="last"
                    value={last || ''}
                    onChange={this.handleChange}
                    placeholder="Last Name"
                  />
                </div>
              </div>
              <ControlLabel bsClass="label-margin">Phone</ControlLabel>
              <FormControl
                type="text"
                id="phone"
                value={phone || ''}
                onChange={this.handleChange}
                placeholder="Phone"
              />
              <div className="adjacent">
                <div className="adjacent-column">
                  <ControlLabel bsClass="label-margin">Title</ControlLabel>
                  <FormControl
                    type="text"
                    id="title"
                    value={title || ''}
                    onChange={this.handleChange}
                    placeholder="Title"
                  />
                </div>
                <div className="adjacent-column adjacent-column--prep">at</div>
                <div className="adjacent-column adjacent-column--company">
                  <ControlLabel bsClass="label-margin">Company</ControlLabel>
                  <FormControl
                    type="text"
                    id="company"
                    value={company || ''}
                    onChange={this.handleChange}
                    placeholder="Company"
                  />
                </div>
              </div>
            </FormGroup>
          </div>
          <div className="edit-profile-section">
            <span className="edit-profile-section-title">Change Password</span>
            <FormGroup>
              <ControlLabel bsClass="label-margin">Old Password</ControlLabel>
              <FormControl
                ref="oldpass"
                id="oldpass"
                value={oldpass || ''}
                onChange={this.handleChange}
                type="password"
                autoComplete="off"
                placeholder="Old Password"
              />
              <ControlLabel bsClass="label-margin">New Password</ControlLabel>
              <FormControl
                ref="newpass"
                id="newpass"
                value={newpass || ''}
                onChange={this.handleChange || ''}
                type="password"
                autoComplete="off"
                placeholder="New Password"
              />
              <ControlLabel bsClass="label-margin">Confirm Password</ControlLabel>
              <FormControl
                ref="confirmnewpass"
                id="confirmnewpass"
                value={confirmnewpass || ''}
                onChange={this.handleChange}
                type="password"
                autoComplete="off"
                placeholder="Confirm New Password"
              />
            </FormGroup>
          </div>
          <div className="edit-profile-section">
            <UpdateButtons
              onUpdate={this.props.editUser}
              onCancel={this.props.setProjectView} />
          </div>
        </div>
      </div>
    );
  }
});


const EditProfile = React.createClass({
  getInitialState() {
    const user = this.props.user.toJS();
    return {
      first: user.first_name,
      first_error: false,
      last: user.last_name,
      last_error: false,
      phone: user.phone,
      title: user.job_title,
      company: user.company,
      oldpass: null,
      newpass: null,
      confirmnewpass: null,
      profileSrc: null,
    };
  },

  componentWillReceiveProps(nextProps) {
    const user = nextProps.user.toJS();

    this.setState({
      first: user.first_name,
      first_error: false,
      last: user.last_name,
      last_error: false,
      phone: user.phone,
      title: user.job_title,
      company: user.company,
      oldpass: null,
      newpass: null,
      confirmnewpass: null,
      profileSrc: null
    })
  },

  /* POST the edited user to the API or warn of empty name input*/
  editUser() {
    const { dispatch } = this.props;
    if (!this.state.first || !this.state.last) {
      dispatch(Notification.error('Name fields are required.'));
      var ferror, lerror;
      if (!this.state.first) {
        ferror = true;
      }
      if (!this.state.last) {
        lerror = true;
      }
      this.setState({
        first_error: ferror,
        last_error: lerror
      });
    } else {
      const userData = {
        first_name: this.state.first,
        last_name: this.state.last,
        phone: this.state.phone,
        job_title: this.state.title,
        company: this.state.company,
        password: this.state.oldpass,
        new_password: this.state.newpass,
        confirm_password: this.state.confirmnewpass,
      };

      //only submit an avatar if it has changed
      if (this.state.profileSrc) {
        userData['avatar'] = this.state.profileSrc;
      }

      const { dispatch } = this.props;
      dispatch(updateProfileData(userData))
        .then(() => this.props.setProjectView());
    }
  },

  changeFormState(key, val, callback) {
    const stateChg = {};
    stateChg[key] = val;
    this.setState(stateChg, callback);
  },

  render() {
    const { isInitialized } = this.props;

    if (!isInitialized) {
      return (
        <div className="spinner-container">
          <div className="summary-topbar loading">
            <Spinner inline /> Loading data
          </div>
        </div>
      )
    }

    return (
      <div className="columns">
        <EditAvatarForm
          editUser={this.editUser}
          user={this.props.user}
          setProjectView={this.props.setProjectView}
          changeFormState={this.changeFormState}
        />
        <EditProfileForm
          {...this.state}
          editUser={this.editUser}
          setProjectView={this.props.setProjectView}
          changeFormState={this.changeFormState}
          user={this.props.user}
        />
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    user: state.user,
    isInitialized: (
      state.user.get('isInitialized')
    ),
    setProjectView: () => hashHistory.push('projects')
  }
};

export default connect(mapStateToProps)(EditProfile)
