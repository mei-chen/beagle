var React = require('react');
var Button = require('react-bootstrap/lib/Button');

var { ProjectActions } = require('account/actions');

require('./styles/TableSharedUsers.scss');   //stylings for component


var TableSharedUsers = React.createClass({

  addUser() {
    var inviteNode = this.refs.invite.getDOMNode();
    var email = inviteNode.value;
    var uuid = this.props.uuid;
    ProjectActions.inviteUser(uuid, email);
    inviteNode.value = '';  //clear input element
  },

  render() {
    return (
      <div className="table-shared-users-container">
        <Button onClick={this.addUser}>Add</Button>
        <input ref="invite"
          autoComplete="off"
          placeholder="Search email of existing user"
          type="text"
          name="username"
          id="usernameSearch"
          className="shared-users-searchbar"
        />
      </div>
    );
  }

});


module.exports = TableSharedUsers;
